import json
import sys
import logging


def get_stack_str(stack, stack_pointer):
    result = ""

    max_width = len(str(len(stack))) + len('-2147483648') + len('|') * 2

    for i, val in enumerate(stack):
        # convert negative values to two's complement representation
        if i == 0x3E8:
            result += "--------------\n"
        if (i == 0x800 or i == 0x801) or i <= stack_pointer or (val != 0 and i >= 0x3E8):
            hex_str = f'0x{i + 0:03x}'
            result += f'|{hex_str}|{val:11d}|\n'.ljust(max_width)

    return result


class HTLInterrupt(Exception):
    pass


# 12-bit addresses
# 32-bit values
class RAM:
    def __init__(self):
        self.stack = [0] * 0xFFF
        self.ad = 0x000

    def init_stack(self, data):
        data_start = 0x800
        for value in data:
            self.stack[data_start] = value
            data_start += 1

    def latch_address(self, address):
        assert 0x000 <= address <= 0xFFF, f'RAM: address {hex(address)} out of bounds'
        self.ad = address

    def set(self, value):
        assert -2147483648 <= value <= 2147483647, "Attempt to put in RAM value that out of bounds"
        self.stack[self.ad] = value

    def get(self):
        return self.stack[self.ad]


# Performs operations on its left and right inputs. Where to transfer output decides Control unit
class ALU:
    LEFT_IN = "left_in"
    RIGHT_IN = "right_in"

    def __init__(self):
        self.overflow_flag = False
        self.zero_flag = False
        self.negative_flag = False

        self.r_in = 0
        self.l_in = 0

        self.out = 0

    def set_R_in(self, value):
        self.r_in = value

    def set_L_in(self, value):
        self.l_in = value

    def INC(self):
        self.out = self.r_in + 1

    def DEC(self):
        self.out = self.r_in - 1

    def ADD(self):
        if self.l_in + self.r_in > 0x7FFFFFFF:  # max value is 2147483647
            self.out = -((self.r_in + 1) - (0x7FFFFFFF - self.l_in))
            self.overflow_flag = True
            logging.warning("ALU ADD OPERATION: POSITIVE OVERFLOW")
        elif self.l_in + self.r_in < -0x80000000:  # min value is -2147483648
            self.out = -((self.r_in + 1) - (-0x80000000 - self.l_in))
            self.overflow_flag = True
            logging.warning("ALU ADD OPERATION: NEGATIVE OVERFLOW")
        else:
            self.out = self.l_in + self.r_in
            self.overflow_flag = False

        self.negative_flag = self.out < 0
        self.zero_flag = self.out == 0

    def MUL(self):
        if self.l_in * self.r_in > 0x7FFFFFFF:  # max value is 2147483647
            self.out = -((self.r_in + 1) - (0x7FFFFFFF - self.l_in))
            self.overflow_flag = True
            logging.warning("ALU MUL OPERATION: POSITIVE OVERFLOW")
        elif self.l_in * self.r_in < -0x80000000:  # min value is -2147483648
            self.out = -((self.r_in + 1) - (-0x80000000 - self.l_in))
            self.overflow_flag = True
            logging.warning("ALU MUL OPERATION: NEGATIVE OVERFLOW")
        else:
            self.out = self.l_in * self.r_in
            self.overflow_flag = False

        self.negative_flag = self.out < 0
        self.zero_flag = self.out == 0

    def DIV(self):
        if self.r_in == 0:
            raise ZeroDivisionError

        self.out = int(self.l_in / self.r_in)

        self.negative_flag = self.out < 0
        self.zero_flag = self.out == 0

    def SUB(self):
        self.r_in = -self.r_in
        self.ADD()

    def MOD(self):
        self.out = self.l_in % self.r_in

        self.negative_flag = self.out < 0
        self.zero_flag = self.out == 0

    def transfer(self, from_in=None):
        assert (from_in is not None) and (from_in == self.LEFT_IN or from_in == self.RIGHT_IN)
        if from_in == self.LEFT_IN:
            self.out = self.l_in
        else:
            self.out = self.r_in

        self.negative_flag = self.out < 0
        self.zero_flag = self.out == 0


class ControlUnit:
    def __init__(self, program, init_data, input_buffer, output_buffer):
        self._tick = 0

        self.input_buffer = input_buffer
        self.output_buffer = output_buffer

        self.pc = 0
        self.sp = -1

        self.acc = 0
        self.of = 0  # ovelfow-flag

        self.instructions = program
        self.address_vent_open = False
        self.decoder = {
            "opcode": None,
            "address": None,
            "related_token_index": None
        }

        self.RAM = RAM()
        self.RAM.init_stack(init_data)

        self.alu = ALU()

    def zero_flag(self):
        return self.acc == 0

    def log_state(self):
        logging.debug(
            "tick = %04d -> PC: 0x%03x | SP: 0x%03x | AC: %+06d | ALU flags: zf=%5r nf=%5r of=%5r | RAM addr:0x%03x ||| "
            "related token index: %d",
            self._tick,
            self.pc,
            self.sp,
            self.acc,
            self.alu.zero_flag, self.alu.negative_flag, self.alu.overflow_flag,
            self.RAM.ad,
            self.decoder["related_token_index"])
        # logging.debug("STACK:")
        # logging.debug("%s", get_stack_str(self.sp))

    def tick(self):
        self.log_state()
        self._tick += 1

    def instruction_fetch(self):
        logging.info("=====   instruction fetch   =====")

        if self.address_vent_open:
            assert self.decoder["address"] is not None, "ADDRESS VENT OPEN, BUT INSTRUCTION IN NON ADDRESS"
            self.pc += self.decoder["address"]
            self.address_vent_open = False

        self.decoder = self.instructions[self.pc]

        logging.debug("decoded instruction opcode: %s", self.decoder["opcode"])

        self.pc += 1
        self._tick += 1
        return self.decoder

    def execute(self, instruction):
        opcode = instruction["opcode"]

        if opcode == "PUSH":
            logging.info("----- PUSH -----")
            # sp -> alu --(+1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.INC()
            self.sp = self.alu.out
            self.tick()

            # decoder.address -> ad
            self.RAM.latch_address(instruction["address"])
            self.tick()

            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()

            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()

            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "SET":
            logging.debug("----- SET -----")
            # sp -> alu --(-1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> ad
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()
            # sp -> alu --(-1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.sp = self.alu.out
            self.tick()
            # sp -> alu --(-1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.sp = self.alu.out
            self.tick()

        elif opcode == "GET":
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> ad
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "CMP":  # doesn't affect on stack pointer and stack itself
            logging.debug("----- CMP -----")
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu --(-1) -> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu --(sub)--> acc
            self.alu.set_L_in(self.acc)
            self.alu.set_R_in(self.RAM.get())
            self.alu.SUB()
            self.acc = self.alu.out
            self.tick()
            # after upper code ZF can be True if numbers equal and FALSE if not

        elif opcode == "JMP":
            logging.debug("----- JMP -----")
            # decoder_address -> alu -> pc
            self.address_vent_open = True
            self.tick()

        elif opcode == "JZ":
            logging.debug("----- JZ -----")
            # decoder_address -> alu -> pc
            if self.alu.zero_flag is True:
                self.address_vent_open = True
            self.tick()

        elif opcode == "JNZ":
            logging.debug("----- JNZ -----")
            # decoder_address -> alu -> pc
            if self.alu.zero_flag is False:
                self.address_vent_open = True
            self.tick()

        elif opcode == "JL":
            logging.debug("----- JL -----")
            # decoder_address -> alu -> pc
            if self.alu.negative_flag is True:
                self.address_vent_open = True
            self.tick()

        elif opcode in {"ADD", "SUB", "MOD", "DIV", "MUL"}:
            logging.debug("----- ADD/SUB/MOD/DIV/MUL -----")
            # sp -> alu --(-1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()

            # acc -------+ l_in
            #            |----> alu --(add/sub/mod/div/mul)--> acc
            # data[ad] --+ r_in
            self.alu.set_L_in(self.acc)
            self.alu.set_R_in(self.RAM.get())

            if opcode == "ADD":
                self.alu.ADD()
            elif opcode == "SUB":
                self.alu.SUB()
            elif opcode == "MOD":
                self.alu.MOD()
            elif opcode == "MUL":
                self.alu.MUL()
            elif opcode == "DIV":
                self.alu.DIV()

            self.acc = self.alu.out
            self.tick()

            # sp -> alu --(-1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.sp = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "SWAP":
            logging.debug("----- SWAP -----")
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu --(+1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.INC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()
            # sp -> alu --(-1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()
            # sp -> alu --(+1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.INC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu --(-1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "DUP":
            logging.debug("----- DUP -----")
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu --(+1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.INC()
            self.sp = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "DROP":
            logging.debug("----- DROP -----")
            # sp -> alu --(-1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.sp = self.alu.out
            self.tick()

        elif opcode == "OVER":
            logging.debug("----- OVER -----")
            # sp -> alu --(-1)--> ad
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> acc
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.acc = self.alu.out
            self.tick()
            # sp -> alu --(+1) --> sp
            self.alu.set_R_in(self.sp)
            self.alu.INC()
            self.sp = self.alu.out
            self.tick()
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # acc -> alu -> data[ad]
            self.alu.set_L_in(self.acc)
            self.alu.transfer(from_in=ALU.LEFT_IN)
            self.RAM.set(self.alu.out)
            self.tick()

        elif opcode == "PRINT":
            logging.debug("----- PRINT -----")
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> out_buffer
            self.output_buffer.append(self.RAM.get())
            self.tick()
            # sp -> alu --(-1)--> sp
            self.alu.set_R_in(self.sp)
            self.alu.DEC()
            self.sp = self.alu.out
            self.tick()

        elif opcode == "READ":
            # sp -> alu -> ad
            self.alu.set_R_in(self.sp)
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # data[ad] -> alu -> ad
            self.alu.set_R_in(self.RAM.get())
            self.alu.transfer(from_in=ALU.RIGHT_IN)
            self.RAM.latch_address(self.alu.out)
            self.tick()
            # input_buffer -> data[ad]
            if len(self.input_buffer) < 1:
                raise BufferError("Attempt to read from void input buffer")

            char = self.input_buffer.pop(0)
            self.RAM.set(char)

        elif opcode == "HLT":
            logging.debug("----- HLT -----")
            raise HTLInterrupt("HTLInterrupt")


class Simpulation:
    def simulate(self):
        with open("../program.bin", encoding="utf-8") as program_file:
            program = json.loads(program_file.read())
            instructions, data = program["instructions"], program["data"]
            print(instructions)

            input_buffer = []
            with open("../in.txt", "r") as input_file:
                string = input_file.read()
                for token in string:
                    input_buffer.append(ord(token))

                input_buffer.append(0)

            output_buffer = []

            cu = ControlUnit(instructions, data, input_buffer, output_buffer)

            instruction_counter = 0
            while True:
                try:
                    decoded_instruction = cu.instruction_fetch()
                    cu.execute(decoded_instruction)

                    instruction_counter += 1

                except HTLInterrupt:
                    logging.info("HLT INTERRUPTION")
                    break

            logging.info("INSTRUCTION COUNTER: %d", instruction_counter)

            print("STACK:")
            print(get_stack_str(cu.RAM.stack, cu.sp))

            ascii_codes = cu.output_buffer
            characters = [chr(code) for code in ascii_codes]
            string = ''.join(characters)
            with open("../out.txt", "w") as file:
                file.write(string)


def main(args):
    simulation = Simpulation()
    simulation.simulate()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
