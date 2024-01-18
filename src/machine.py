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

    def __init__(self):
        self.overflow_flag = False
        self.zero_flag = False
        self.negative_flag = False

    def INC(self, value):
        return value + 1

    def DEC(self, value):
        return value - 1

    def ADD(self, l_in, r_in):
        if l_in + r_in > 0x7FFFFFFF:  # max value is 2147483647
            logging.warning("ALU ADD OPERATION: POSITIVE OVERFLOW")
            self.overflow_flag = True
            out = -((r_in + 1) - (0x7FFFFFFF - l_in))
        elif l_in + r_in < -0x80000000:  # min value is -2147483648
            logging.warning("ALU ADD OPERATION: NEGATIVE OVERFLOW")
            self.overflow_flag = True
            out = -((r_in + 1) - (-0x80000000 - l_in))
        else:
            self.overflow_flag = False
            out = l_in + r_in

        self.negative_flag = out < 0
        self.zero_flag = out == 0

        return out

    def MUL(self, l_in, r_in):
        if l_in * r_in > 0x7FFFFFFF:  # max value is 2147483647
            logging.warning("ALU MUL OPERATION: POSITIVE OVERFLOW")
            out = -((r_in + 1) - (0x7FFFFFFF - l_in))
            self.overflow_flag = True
        elif l_in * r_in < -0x80000000:  # min value is -2147483648
            logging.warning("ALU MUL OPERATION: NEGATIVE OVERFLOW")
            self.overflow_flag = True
            out = -((r_in + 1) - (-0x80000000 - l_in))
        else:
            out = l_in * r_in
            self.overflow_flag = False

        self.negative_flag = out < 0
        self.zero_flag = out == 0

        return out

    def DIV(self, l_in, r_in):
        if r_in == 0:
            raise ZeroDivisionError

        out = int(l_in / r_in)

        self.negative_flag = out < 0
        self.zero_flag = out == 0

        return out

    def SUB(self, l_in, r_in):
        r_in = -r_in
        return self.ADD(l_in, r_in)

    def MOD(self, l_in, r_in):
        out = l_in % r_in

        self.negative_flag = out < 0
        self.zero_flag = out == 0

        return out

    def transfer(self, l_in_or_r_in):
        out = l_in_or_r_in

        self.negative_flag = out < 0
        self.zero_flag = out == 0

        return out


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
            # sp -> alu --(+1)--> sp; decoder.address -> ad
            self.sp = self.alu.INC(self.sp)
            self.RAM.latch_address(instruction["address"])
            self.tick()

            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()

            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()

            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "SET":
            logging.debug("----- SET -----")
            # sp -> alu --(-1)--> ad
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.RAM.get()))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()
            # sp -> alu --(-1)--> sp
            self.sp = self.alu.DEC(self.sp)
            self.tick()
            # sp -> alu --(-1)--> sp
            self.sp = self.alu.DEC(self.sp)
            self.tick()

        elif opcode == "GET":
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.RAM.get()))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "CMP":  # doesn't affect on stack pointer and stack itself
            logging.debug("----- CMP -----")
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu --(-1) -> ad
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # data[ad] -> alu --(sub)--> acc
            self.acc = self.alu.SUB(self.acc, self.RAM.get())
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
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()

            # acc -------+ l_in
            #            |----> alu --(add/sub/mod/div/mul)--> acc
            # data[ad] --+ r_in

            if opcode == "ADD":
                self.acc = self.alu.ADD(self.acc, self.RAM.get())
            elif opcode == "SUB":
                self.acc = self.alu.SUB(self.acc, self.RAM.get())
            elif opcode == "MOD":
                self.acc = self.alu.MOD(self.acc, self.RAM.get())
            elif opcode == "MUL":
                self.acc = self.alu.MUL(self.acc, self.RAM.get())
            elif opcode == "DIV":
                self.acc = self.alu.DIV(self.acc, self.RAM.get())

            self.tick()

            # sp -> alu --(-1)--> sp
            self.sp = self.alu.DEC(self.sp)
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "SWAP":
            logging.debug("----- SWAP -----")
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu --(+1)--> ad
            self.RAM.latch_address(self.alu.INC(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()
            # sp -> alu --(-1)--> ad
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()
            # sp -> alu --(+1)--> ad
            self.RAM.latch_address(self.alu.INC(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu --(-1)--> ad
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "DUP":
            logging.debug("----- DUP -----")
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu --(+1)--> sp
            self.sp = self.alu.INC(self.sp)
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "DROP":
            logging.debug("----- DROP -----")
            # sp -> alu --(-1)--> sp
            self.sp = self.alu.DEC(self.sp)
            self.tick()

        elif opcode == "OVER":
            logging.debug("----- OVER -----")
            # sp -> alu --(-1)--> ad
            self.RAM.latch_address(self.alu.DEC(self.sp))
            self.tick()
            # data[ad] -> alu -> acc
            self.acc = self.alu.transfer(self.RAM.get())
            self.tick()
            # sp -> alu --(+1) --> sp
            self.sp = self.alu.INC(self.sp)
            self.tick()
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # acc -> alu -> data[ad]
            self.RAM.set(self.alu.transfer(self.acc))
            self.tick()

        elif opcode == "PRINT":
            logging.debug("----- PRINT -----")
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> out_buffer
            self.output_buffer.append(self.RAM.get())
            self.tick()
            # sp -> alu --(-1)--> sp
            self.sp = self.alu.DEC(self.sp)
            self.tick()

        elif opcode == "READ":
            # sp -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.sp))
            self.tick()
            # data[ad] -> alu -> ad
            self.RAM.latch_address(self.alu.transfer(self.RAM.get()))
            self.tick()
            # input_buffer -> data[ad]
            if len(self.input_buffer) < 1:
                raise BufferError("Attempt to read from void input buffer")

            char = self.input_buffer.pop(0)
            self.RAM.set(char)
            self.tick()

        elif opcode == "HLT":
            logging.debug("----- HLT -----")
            raise HTLInterrupt("HTLInterrupt")


class Simulation:
    def __init__(self, program, input_buffer, output_buffer):
        self.instructions = program["instructions"]
        self.data = program["data"]

        self.input_buffer = input_buffer
        self.output_buffer = output_buffer

    def simulate(self):
        cu = ControlUnit(self.instructions, self.data, self.input_buffer, self.output_buffer)

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


def main(program_file_path, input_file_path, output_file_path):

    with open(program_file_path, encoding="utf-8") as program_file:
        program = json.loads(program_file.read())

        input_buffer = []
        with open(input_file_path, "r") as input_file:
            string = input_file.read()
            for token in string:
                input_buffer.append(ord(token))

            input_buffer.append(0)

            output_buffer = []

            simulation = Simulation(program, input_buffer, output_buffer)
            simulation.simulate()

            characters = [chr(code) for code in output_buffer]
            string = ''.join(characters)
            with open(output_file_path, "w") as file:
                file.write(string)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
