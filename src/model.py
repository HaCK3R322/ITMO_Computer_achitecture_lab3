# up to 2^16 of 8-bit values
class Stack:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.sp = 0xFFFE
        self.tos = 0x00

    def get_next(self):
        # not exactly next, but returns value from stack by SP
        assert self.sp != 0xFFFE and self.sp != 0xFFFF, f'STACK ERROR: trying to get forbidden address (sp = {self.sp})'
        return self.data[self.sp]

    def get_tos(self):
        return self.tos

    def sp_inc(self):
        self.sp += 1

        if self.sp == (0xFFFF + 1):
            self.sp = 0x0000

    def sp_dec(self):
        self.sp -= 1

        if self.sp == -1:
            self.sp = 0xFFFF

    def push(self, value):
        self.sp_inc()
        self.data[self.sp] = self.tos
        assert -128 <= value <= 255, f'STACK: push filed with value {value}'
        self.tos = value

    def pop(self):
        old_tos_value = self.tos
        self.tos = self.data[self.sp]
        self.sp_dec()
        return old_tos_value

    def write_tos_to_sp(self):
        self.data[self.sp] = self.tos

    def print_stack(self):
        if self.sp < 0xFFFD:
            for address in range(self.sp + 1):
                decimal_representation = self.data[address] if self.data[address] < 128 else self.data[address] - 256
                print(f"0x{address:04X} | 0x{self.data[address]:02X}  ==  {decimal_representation}", end="")
                if self.sp == address:
                    print(" <--")
                else:
                    print()
        print('-------------')
        decimal_representation = self.tos if self.tos < 128 else self.tos - 256
        print(f" TOS   | 0x{self.tos:02X}  ==  {decimal_representation}")
        print()


class RAM:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.ad = 0x0000

    def init_data(self, data):
        data_start = 0x0000
        for value in data:
            self.data[data_start] = value
            data_start += 1

    def latch_address(self, address):
        assert 0x0000 <= address <= 0xFFFF, f'RAM: address {hex(address)} out of bounds'
        self.ad = address

    def latch_address_low_bits(self, address_low_bits):
        assert 0x00 <= address_low_bits <= 0xFF, f'RAM: address low bits {hex(address_low_bits)} out of bounds'
        self.ad = (self.ad & 0xFF00) + address_low_bits

    def latch_address_high_bits(self, address_high_bits):
        assert 0x00 <= address_high_bits <= 0xFF, f'RAM: address low bits {hex(address_high_bits)} out of bounds'
        self.ad = (self.ad & 0x00FF) + address_high_bits * 0x100

    def save(self, value):
        assert 0 <= value <= 255, "Attempt to put in RAM value that out of bounds"
        self.data[self.ad] = value

    def load(self):
        return self.data[self.ad]


class InstructionsMemory:
    def __init__(self):
        self.data = [{"value": 0x00, "related_token_index": -1}] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.address = 0x0000

    def init_data(self, data):
        data_start = 0x0000
        for value in data:
            self.data[data_start] = value
            data_start += 1

    def address_inc(self):
        assert self.address < 0xFFFF, f'PC INC error: out of bounds (pc currently is 0xFFFF)'
        self.address += 1

    def latch_address(self, new_address):
        assert 0x0000 <= new_address <= 0xFFFF, f'INSTRUCTION MEMORY: address {hex(new_address)} out of bounds'
        self.address = new_address

    def latch_address_low_bits(self, address_low_bits):
        assert 0x00 <= address_low_bits <= 0xFF, f'INSTRUCTION MEMORY: address low bits {hex(address_low_bits)} out of bounds'
        self.address = (self.address & 0xFF00) + address_low_bits

    def latch_address_high_bits(self, address_high_bits):
        assert 0x00 <= address_high_bits <= 0xFF, f'INSTRUCTION MEMORY: address low bits {hex(address_high_bits)} out of bounds'
        self.address = (self.address & 0x00FF) + address_high_bits * 0x100

    def load(self):
        return self.data[self.address]


class Decoder:
    def __init__(self):
        self.instruction = None
        self.opcode = None
        self.operand = None

        self.__non_address_instructions_list = [
            "RET", "SWAP", "OVER", "DUP", "DROP", "ROT", "TOR", "RFROM", "SET", "GET", "SUM", "SUB", "DIV", "MUL",
            "MOD", "INC", "DEC", "HLT"
        ]
        self.__address_instructions_list = [
            "LOAD", "SAVE", "JMP", "JZ", "JL", "JO", "CALL"
        ]

    def __is_address_instruction(self):
        return self.instruction["value"] in self.__address_instructions_list

    def decode(self):
        if self.__is_address_instruction():
            if not 0b00000 <= self.instruction["address"] <= 0b11111:
                raise AssertionError(f'DECODER: operand of address instruction is out of bounds: {self.instruction["address"]}')
            self.opcode = self.instruction["value"]
            self.operand = self.instruction["address"]
        else:
            if not self.instruction["value"] in self.__non_address_instructions_list:
                raise AssertionError(f'DECODER: unknown OPCODE: {self.instruction["value"]}')
            self.opcode = self.instruction["value"]


class ControlUnit:
    def __init__(self):
        self.pc = 0

        self.stack = Stack()
        self.rstack = Stack()
        self.ram = RAM()
        self.imem = InstructionsMemory()

        self.decoder = Decoder()

        self.of = False
        self.zf = False
        self.nf = False

        self.ticks = 0

    def get_stack_str(self, stack):
        a = stack.sp - 3 if stack.sp - 3 > -1 else 999999
        b = stack.sp - 2 if stack.sp - 2 > -1 else 999999
        c = stack.sp - 1 if stack.sp - 1 > -1 else 999999
        d = stack.sp if stack.sp - 1 > -1 else 999999

        aa = f'0x{stack.data[a]:02X}' if a != 999999 and stack.data[a] != 0 else '    '
        bb = f'0x{stack.data[b]:02X}' if b != 999999 and stack.data[b] != 0 else '    '
        cc = f'0x{stack.data[c]:02X}' if c != 999999 and stack.data[c] != 0 else '    '
        dd = f'0x{stack.data[d]:02X}' if d != 999999 and stack.data[d] != 0 else '    '

        tos = f'0x{self.stack.tos:02X}' if stack.sp != 65534 else '    '

        return f'{aa} {bb} {cc} {dd} , {tos}'

    def print_state(self):
        print(f'tick {self.ticks: >6}: STACK(sp=={self.stack.sp: >5}): |',
              self.get_stack_str(self.stack),
              '|',
              f'     RSTACK(sp=={self.rstack.sp: >5}): |',
              self.get_stack_str(self.rstack),
              '|    ',
              f'ZF/NF/OF: {self.zf:1}/{self.nf:1}/{self.of:1}'
              )

    def tick(self):
        self.ticks += 1
        self.print_state()

    def latch_pc_low_bits(self, address_low_bits):
        assert 0x00 <= address_low_bits <= 0xFF, f'INSTRUCTION MEMORY: address low bits {hex(address_low_bits)} out of bounds'
        self.pc = (self.pc & 0xFF00) + address_low_bits

    def latch_pc_high_bits(self, address_high_bits):
        assert 0x00 <= address_high_bits <= 0xFF, f'INSTRUCTION MEMORY: address low bits {hex(address_high_bits)} out of bounds'
        self.pc = (self.pc & 0x00FF) + address_high_bits * 0x100

    # LOGICAL OPERATIONS
    def tor(self):
        """
        rsp++; TOS -> RSTACK[rsp];sp--
        """
        self.rstack.push(self.stack.pop())
        self.tick()

    def rfrom(self):
        """
        sp++; RSTACK[rsp] -> TOS; rsp--;
        """
        self.stack.push(self.rstack.pop())
        self.tick()

    def dup(self):
        self.stack.sp_inc()
        self.stack.write_tos_to_sp()
        self.tick()

    def drop(self):
        self.stack.pop()
        self.tick()

    def over(self):
        """
        sp++\n
        stack[sp] = TOS\n
        sp--\n
        TOS = stack[sp]\n
        SP++\n
        """
        self.stack.sp_inc()
        self.tick()
        self.stack.data[self.stack.sp] = self.stack.tos
        self.tick()
        self.stack.sp_dec()
        self.tick()
        self.stack.tos = self.stack.data[self.stack.sp]
        self.tick()
        self.stack.sp_inc()
        self.tick()

    def swap(self):
        """
        OVER();\n
        >r;\n
        >r;\n
        DROP();\n
        r>;\nr>\n
        """
        self.over()
        self.tor()
        self.tor()
        self.drop()
        self.rfrom()
        self.rfrom()

    def rot(self):
        """
        >r;\n
        SWAP();\n
        r>;\n
        SWAP();
        """
        self.tor()
        self.swap()
        self.rfrom()
        self.swap()

    def inc(self):
        self.stack.tos += 1
        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick()

    def dec(self):
        self.stack.tos -= 1
        if self.stack.tos < 0:
            self.stack.tos += 0x100
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick()

    def sum(self):
        """
        tos + stack[sp] => tos; sp--
        """
        self.stack.tos = self.stack.tos + self.stack.get_next()

        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.stack.sp_dec()

        self.tick()

    def sub(self):
        """
        tos - stack[sp] => tos; sp--
        """
        self.stack.tos = self.stack.get_next() - self.stack.tos
        if self.stack.tos < 0:
            self.stack.tos += 0x100

        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False
        self.of = False  # Reset overflow flag for subtraction

        self.stack.sp_dec()

        self.tick()

    def mul(self):
        """
        tos * stack[sp] => tos; sp--
        """
        result_unsigned = self.stack.tos * self.stack.get_next()

        # If either operand is negative, adjust the result
        if (self.stack.tos & 0x80) != 0 and (self.stack.get_next() & 0x80) != 0:
            # Both operands are negative, result needs adjustment
            result_signed = -(0x100 - result_unsigned)
        elif (self.stack.tos & 0x80) != 0 or (self.stack.get_next() & 0x80) != 0:
            # One operand is negative, result needs adjustment
            result_signed = result_unsigned - 0x100
        else:
            # Both operands are positive, no adjustment needed
            result_signed = result_unsigned

        # Update TOS with the result
        self.stack.tos = result_signed & 0xFF

        # Set flags based on the result
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False
        self.of = True if result_signed > 0x7F or result_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def divide(self):
        """
        stack[sp] / tos => tos; sp--
        """
        divisor = self.stack.tos

        if divisor == 0:
            # Division by zero, handle error or set flags accordingly
            # For simplicity, let's set the result to 0 and flags to indicate an error
            self.stack.tos = 0
            self.zf = True
            self.nf = False
            self.of = True  # Indicate division by zero error
        else:
            # Perform division treating the numbers as signed integers
            quotient_signed = self.stack.get_next() // divisor

            # Update TOS with the quotient
            self.stack.tos = quotient_signed & 0xFF

            # Set flags based on the result
            self.zf = True if self.stack.tos == 0 else False
            self.nf = True if self.stack.tos >= 0x80 else False
            self.of = True if quotient_signed > 0x7F or quotient_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def mod(self):
        """
        stack[sp] % tos => tos; sp--
        """
        divisor = self.stack.tos

        if divisor == 0:
            # Division by zero, handle error or set flags accordingly
            # For simplicity, let's set the result to 0 and flags to indicate an error
            self.stack.tos = 0
            self.zf = True
            self.nf = False
            self.of = True  # Indicate division by zero error
        else:
            # Perform division treating the numbers as signed integers
            quotient_signed = self.stack.get_next() % divisor

            # Update TOS with the quotient
            self.stack.tos = quotient_signed & 0xFF

            # Set flags based on the result
            self.zf = True if self.stack.tos == 0 else False
            self.nf = True if self.stack.tos >= 0x80 else False
            self.of = True if quotient_signed > 0x7F or quotient_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def set(self):
        """
        TOS -> AD_L; sp--;\n
        TOS -> AD_H; sp--;\n
        TOS -> RAM[AD]; sp--;
        """
        self.ram.latch_address_low_bits(self.stack.pop())
        self.tick()
        self.ram.latch_address_high_bits(self.stack.pop())
        self.tick()
        self.ram.save(self.stack.pop())
        self.tick()

    def get(self):
        """
        TOS -> AD_L; sp--;\n
        TOS -> AD_H; sp--;\n
        sp++; RAM[AD] -> TOS;
        """
        self.ram.latch_address_low_bits(self.stack.pop())
        self.tick()
        self.ram.latch_address_high_bits(self.stack.pop())
        self.tick()
        self.stack.push(self.ram.load())
        self.tick()

    def load(self):
        print("Executing LOAD instruction")

    def save(self):
        print("Executing SAVE instruction")

    def __opcode_and_address_to_bits(self):
        """
        address structure:
        address bits #15 to #9: 0\n
        address bits  #8 to #6: OPCODE bits\n
        address bits  #5 to #1: OFFSET bits\n
        address bit         #0: 0\n
        :return: computed address
        """

        opcode_bit_map = {
            "LOAD": 0b000,
            "SAVE": 0b001,
            "JMP": 0b010,
            "JZ": 0b011,
            "JL": 0b100,
            "JO": 0b101,
            "CALL": 0b110,
        }
        opcode_bits = (opcode_bit_map[self.decoder.opcode] << 6) & 0x1C0
        offset_bits = (self.decoder.operand & 0x1F) << 1

        return opcode_bits | offset_bits

    def jmp(self):
        """
        - compute address from OPCODE and OFFSET -> IMEM.ADDRESS
        - IMEM[IMEM.ADDRESS] -> PC_High_bits
        - IMEM.ADDRESS inc
        - IMEM[IMEM.ADDRESS] -> PC_Low_bits
        """
        self.imem.latch_address(self.__opcode_and_address_to_bits())
        self.tick()
        self.latch_pc_high_bits(self.imem.load()["value"])
        self.tick()
        self.imem.address_inc()
        self.tick()
        self.latch_pc_high_bits(self.imem.load()["value"])
        self.tick()

    def jz(self):
        print("Executing JZ instruction")

    def jl(self):
        print("Executing JL instruction")

    def jo(self):
        print("Executing JO instruction")

    def call(self):
        print(f'{self.__opcode_and_address_to_bits():016b}')

    def hlt(self):
        raise Exception("HLT was raised")

    def execute(self, opcode):
        opcode_mapping = {
            "TOR": self.tor,
            "RFROM": self.rfrom,
            "DUP": self.dup,
            "DROP": self.drop,
            "OVER": self.over,
            "SWAP": self.swap,
            "ROT": self.rot,
            "INC": self.inc,
            "DEC": self.dec,
            "SUM": self.sum,
            "SUB": self.sub,
            "MUL": self.mul,
            "DIV": self.divide,
            "MOD": self.mod,
            "SET": self.set,
            "GET": self.get,
            "LOAD": self.load,
            "SAVE": self.save,
            "JMP": self.jmp,
            "JZ": self.jz,
            "JL": self.jl,
            "JO": self.jo,
            "CALL": self.call,
            "HLT": self.hlt,
        }

        if opcode not in opcode_mapping:
            raise ValueError(f"Invalid opcode: {opcode}")

        # Call the corresponding method based on the opcode
        opcode_mapping[opcode]()


class Simulation:
    def __init__(self):
        print("-- init method of simulation --")

        self.cu = ControlUnit()

        self.cu.stack.push(0x01)

        self.cu.imem.data[0b11000000] = {"value": 0x02, "related_token_index": 1}
        self.cu.imem.data[0b11000001] = {"value": 0x08, "related_token_index": 1}

        self.cu.imem.data[0x0200] = {"value": "JMP", "address": 0b00000, "related_token_index": 0}
        self.cu.imem.data[0x0201] = {"value": "DUP", "related_token_index": 1}
        self.cu.imem.data[0x0202] = {"value": "DUP", "related_token_index": 1}
        self.cu.imem.data[0x0203] = {"value": "SUM", "related_token_index": 1}
        self.cu.imem.data[0x0204] = {"value": "SWAP", "related_token_index": 1}
        self.cu.imem.data[0x0205] = {"value": "DUP", "related_token_index": 1}
        self.cu.imem.data[0x0206] = {"value": "SUM", "related_token_index": 1}
        self.cu.imem.data[0x0207] = {"value": "MUL", "related_token_index": 1}
        self.cu.imem.data[0x0208] = {"value": "HLT", "related_token_index": -1}

        self.cu.imem.data[0x0209] = {"value": "DUP", "related_token_index": -1}
        self.cu.imem.data[0x020a] = {"value": "DUP", "related_token_index": -1}
        self.cu.imem.data[0x020b] = {"value": "HLT", "related_token_index": -1}

        self.cu.pc = 0x0200
        self.cu.imem.address = 0x0000

    def instruction_fetch(self):
        self.cu.imem.latch_address(self.cu.pc)
        self.cu.decoder.instruction = self.cu.imem.load()

    def decode(self):
        self.cu.decoder.decode()

    def execute(self):
        self.cu.execute(self.cu.decoder.opcode)

    def simulate(self):
        while True:
            self.instruction_fetch()
            self.decode()
            self.execute()
            self.cu.pc += 1


if __name__ == '__main__':
    simulation = Simulation()

    try:
        simulation.simulate()
    except Exception as e:
        print(e)


    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    #
    # cu.add()
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    #
    # cu.add()
    #
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    #
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    #
    # cu.add()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.add()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.stack.sp_dec()
    # cu.tick()
    # cu.over()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.stack.sp_inc()
    # cu.tick()
    # cu.drop()
    # cu.stack.print_stack()
