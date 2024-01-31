import json
import logging
import shutil
from logging.handlers import RotatingFileHandler
import os
import sys
import time


class Stack:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.sp = 0xFFFE
        self.tos = 0x00

    def get_next(self):
        # not exactly next, but returns value from stack by SP
        assert self.sp != 0xFFFE and self.sp != 0xFFFF, f'STACK ERROR: trying to get forbidden address (sp = {self.sp:04X})'
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
        """
        sp++; tos->stack[sp]; value -> tos
        :param value: to push on TOS
        """
        self.sp_inc()
        self.data[self.sp] = self.tos
        assert -128 <= value <= 255, f'STACK: push filed with value {value}'
        self.tos = value

    def pop(self):
        old_tos_value = self.tos
        self.tos = self.data[self.sp]
        self.sp_dec()
        return old_tos_value

    def write_tos_to_next(self):
        """
        no stack pointer manipulation. Only tos -> stack[sp]
        """
        self.data[self.sp] = self.tos

    def write_next_to_tos(self):
        self.tos = self.data[self.sp]

    def swap(self):
        temp = self.tos
        self.tos = self.data[self.sp]
        self.data[self.sp] = temp

    def print_stack(self):
        if self.sp < 0xFFFD:
            for address in range(self.sp + 1):
                decimal_representation = self.data[address] if self.data[address] < 128 else self.data[address] - 256
                logging.log(logging.INFO,
                            f"0x{address:04X} | 0x{self.data[address]:02X}  ==  {decimal_representation} {' <-- ' if self.sp == address else ''}")
        logging.log(logging.INFO, '-------------')
        decimal_representation = self.tos if self.tos < 128 else self.tos - 256
        logging.log(logging.INFO, f" TOS   | 0x{self.tos:02X}  ==  {decimal_representation}")


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
        self.data = [{"value": 0x00, "related_token": "model imem init",
                      "related_token_index": -1}] * 0x10000  # addresses from 0x0000 to 0xFFFF
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
        self.offset = None

        self.__non_address_instructions_list = [
            "RET", "SWAP", "OVER", "DUP", "DROP", "ROT", "TOR", "RFROM", "SET", "GET", "SUM", "SUB", "DIV", "MUL",
            "MOD", "INC", "DEC", "HLT", "TRUE", "FALSE", "CMP", "PRINT", "READ", "TMOD", "TDIV"
        ]
        self.__address_instructions_list = [
            "LOAD", "JMPA", "JMPR", "JZ", "JL", "JO", "CALL"
        ]

    def decode(self):
        if self.instruction["value"] in self.__address_instructions_list:
            self.opcode = self.instruction["value"]
            self.offset = self.instruction["offset"]
        else:
            if not self.instruction["value"] in self.__non_address_instructions_list:
                raise ValueError(
                    f'DECODER: unknown OPCODE: {self.instruction["value"]}, related token: {self.instruction["related_token"]}')
            self.opcode = self.instruction["value"]


class ControlUnit:
    def __init__(self):
        self.pc = 0

        self.stack = Stack()
        self.rstack = Stack()
        self.ram = RAM()
        self.imem = InstructionsMemory()
        self.input_buffer = []
        self.output_buffer = []

        self.decoder = Decoder()

        self.of = False
        self.zf = False
        self.nf = False

        self.ticks = 0

    def get_stack_str(self, stack):
        a = stack.sp - 3 if stack.sp - 3 > -1 else 999999
        b = stack.sp - 2 if stack.sp - 2 > -1 else 999999
        c = stack.sp - 1 if stack.sp - 1 > -1 else 999999
        d = stack.sp if stack.sp > -1 else 999999

        aa = f'0x{stack.data[a]:02X}' if a != 999999 and stack.data[a] != 0 else '    '
        bb = f'0x{stack.data[b]:02X}' if b != 999999 and stack.data[b] != 0 else '    '
        cc = f'0x{stack.data[c]:02X}' if c != 999999 and stack.data[c] != 0 else '    '
        dd = f'0x{stack.data[d]:02X}' if d != 999999 and stack.data[d] != 0 else '    '

        tos = f'0x{stack.tos:02X}' if stack.sp != 65534 else '    '

        return f'{aa} {bb} {cc} {dd} , {tos}'

    def get_state_str(self, instruction_name):
        return (f'tick {self.ticks: >6}: STACK(sp==0x{self.stack.sp:04X}): |' +
                self.get_stack_str(self.stack) +
                '|' +
                f'     RSTACK(sp=={self.rstack.sp: >5}): |' +
                self.get_stack_str(self.rstack) +
                '|    ' +
                f'ZF/NF/OF: {self.zf:1}/{self.nf:1}/{self.of:1}' +
                f'     IMEM.ADDR: 0x{self.imem.address:04x}' +
                f'     PC: 0x{self.pc:04x}' +
                f'     rel_inst_index: {self.decoder.instruction["related_token_index"]} ({self.decoder.instruction["related_token"]}, {instruction_name})')

    def tick(self, instruction_name):
        self.ticks += 1
        logging.log(logging.DEBUG, self.get_state_str(instruction_name))

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
        self.tick("TOR")

    def rfrom(self):
        """
        sp++; RSTACK[rsp] -> TOS; rsp--;
        """
        self.stack.push(self.rstack.pop())
        self.tick("RFROM")

    def dup(self):
        self.stack.sp_inc()
        self.stack.write_tos_to_next()
        self.tick("DUP")

    def drop(self):
        self.stack.pop()
        self.tick("DROP")

    def over(self):
        """
        sp++\n
        stack[sp] = TOS\n
        sp--\n
        TOS = stack[sp]\n
        SP++\n
        """
        self.stack.sp_inc()
        self.tick("OVER")
        self.stack.write_tos_to_next()
        self.tick("OVER")
        self.stack.sp_dec()
        self.tick("OVER")
        self.stack.write_next_to_tos()
        self.tick("OVER")
        self.stack.sp_inc()
        self.tick("OVER")

    def true(self):
        self.stack.push(0b11111111)
        self.tick("TRUE")

    def false(self):
        self.stack.push(0)
        self.tick("FALSE")

    def cmp(self):
        a = self.stack.data[self.stack.sp]
        b = self.stack.tos

        sign_mask = 0b10000000

        sign_a = a & sign_mask
        sign_b = b & sign_mask

        if a == b:
            self.zf = 1
        else:
            self.zf = 0

        if sign_a and not sign_b:
            self.nf = 1  # Set Negative Flag if a is negative and b is positive
        elif not sign_a and sign_b:
            self.nf = 0  # Clear Negative Flag if a is positive and b is negative
        else:
            # Both numbers have the same sign, compare magnitudes
            self.nf = 1 if a < b else 0

        self.tick("CMP")

    def swap(self):
        """
        stack swap
        """
        self.stack.swap()
        self.tick("SWAP")

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
            self.stack.tos = self.stack.tos & 0xFF
            self.of = True
        else:
            self.of = False
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick("INC")

    def dec(self):
        self.stack.tos -= 1
        if self.stack.tos < 0:
            self.stack.tos += 0x100
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick("DEC")

    def sum(self):
        """
        tos + stack[sp] => tos; sp--
        """
        self.stack.tos = self.stack.tos + self.stack.get_next()

        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True
        else:
            self.of = False
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.stack.sp_dec()

        self.tick("SUM")

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

        self.tick("SUB")

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

        self.tick("MUL")

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

        self.tick("DIV")

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

        self.tick("MOD")

    def set(self):
        """
        TOS -> AD_L; sp--;\n
        TOS -> AD_H; sp--;\n
        TOS -> RAM[AD]; sp--;
        """
        self.ram.latch_address_low_bits(self.stack.pop())
        self.tick("SET")
        self.ram.latch_address_high_bits(self.stack.pop())
        self.tick("SET")
        self.ram.save(self.stack.pop())
        self.tick("SET")

        # saved_value = self.ram.load()
        # decimal_representation = saved_value if saved_value < 128 else saved_value - 256
        # print(f'           : RAM[{self.ram.ad:04x}] = {self.ram.load():02X} == ({decimal_representation})')

    def get(self):
        """
        TOS -> AD_L; sp--;\n
        TOS -> AD_H; sp--;\n
        sp++; RAM[AD] -> TOS;
        """
        self.ram.latch_address_low_bits(self.stack.pop())
        self.tick("GET")
        self.ram.latch_address_high_bits(self.stack.pop())
        self.tick("GET")
        self.stack.push(self.ram.load())
        self.tick("GET")

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
            "CALL": 0b001,
            "JMPA": 0b010,
        }
        opcode_bits = (opcode_bit_map[self.decoder.opcode] << 6) & 0x1C0
        offset_bits = (self.decoder.offset & 0x1F) << 1

        return opcode_bits | offset_bits

    def jmp_absolute(self):
        """
        - compute address from OPCODE and OFFSET -> IMEM.ADDRESS
        - IMEM[IMEM.ADDRESS] -> PC_High_bits
        - IMEM.ADDRESS inc
        - IMEM[IMEM.ADDRESS] -> PC_Low_bits
        """
        self.imem.latch_address(self.__opcode_and_address_to_bits())
        self.imem.latch_address(self.__opcode_and_address_to_bits())
        self.tick("JMPA")
        self.latch_pc_high_bits(self.imem.load()["value"])
        self.tick("JMPA")
        self.imem.address_inc()
        self.tick("JMPA")
        self.latch_pc_low_bits(self.imem.load()["value"])
        self.tick("JMPA")

    def jmp_relative(self):
        """
        PC + OFFSET -> PC
        """
        self.pc = self.pc + self.decoder.offset
        self.tick("JMPR")

    def jz(self):
        if self.zf:
            self.jmp_relative()

    def jl(self):
        if self.nf:
            self.jmp_relative()

    def jo(self):
        if self.of:
            self.jmp_relative()
        self.of = False

    def call(self):
        """
        - RSTACK.PUSH(PC_H)
        - RSTACK.PUSH(PC_L)
        - compute address from OPCODE and OFFSET -> IMEM.ADDRESS
        - IMEM[IMEM.ADDRESS] -> PC_High_bits
        - IMEM.ADDRESS inc
        - IMEM[IMEM.ADDRESS] -> PC_Low_bits
        """
        pc_high_bits = (self.pc >> 8) & 0xFF
        self.rstack.push(pc_high_bits)
        self.tick("CALL")
        pc_low_bits = self.pc & 0xFF
        self.rstack.push(pc_low_bits)
        self.tick("CALL")

        self.jmp_absolute()

    def ret(self):
        """
        - RSTACK.POP() *pc low bits* -> PC_Low_bits
        - RSTACK.POP() *pc high bits* -> PC_High_bits
        """
        self.latch_pc_low_bits(self.rstack.pop())
        self.tick("RET")
        self.latch_pc_high_bits(self.rstack.pop())
        self.tick("RET")

    def load(self):
        """
        - compute address from OPCODE and OFFSET -> IMEM.ADDRESS
        - IMEM[IMEM.ADDRESS] -> RAM_ADDRESS_High_bits
        - IMEM.ADDRESS inc
        - IMEM[IMEM.ADDRESS] -> RAM_ADDRESS_Low_bits
        - SP++; TOS -> STACK[SP]; RAM[RAM_ADDRESS] -> TOS
        """
        self.imem.latch_address(self.__opcode_and_address_to_bits())
        self.tick("LOAD")
        self.ram.latch_address_high_bits(self.imem.load()["value"])
        self.tick("LOAD")
        self.imem.address_inc()
        self.tick("LOAD")
        self.ram.latch_address_low_bits(self.imem.load()["value"])
        self.tick("LOAD")

        self.stack.push(self.ram.load())
        self.tick("LOAD")

    def print(self):
        ascii_character = chr(self.stack.pop())
        self.output_buffer.append(ascii_character)
        self.tick("PRINT")

    def read(self):
        if len(self.input_buffer) == 0:
            raise BufferError("Trying to read void input buffer!")
        self.stack.push(self.input_buffer.pop())
        self.tick("READ")

    def tmod(self):
        b3 = self.stack.pop()
        self.tick("TMOD")
        b2 = self.stack.pop() << 8
        self.tick("TMOD")
        b1 = self.stack.pop() << 16
        self.tick("TMOD")
        a3 = self.stack.pop()
        self.tick("TMOD")
        a2 = self.stack.pop() << 8
        self.tick("TMOD")
        a1 = self.stack.pop() << 16
        self.tick("TMOD")

        a = a1 + a2 + a3
        b = b1 + b2 + b3

        if b == 0:
            raise ZeroDivisionError("TMOD div by zero error")
        else:
            c = a % b
            self.stack.push(c >> 16)
            self.tick("TMOD")
            self.stack.push((c >> 8) & 0xFF)
            self.tick("TMOD")
            self.stack.push(c & 0xFF)
            self.tick("TMOD")

    def tdiv(self):
        b3 = self.stack.pop()
        b2 = self.stack.pop() << 8
        b1 = self.stack.pop() << 16
        a3 = self.stack.pop()
        a2 = self.stack.pop() << 8
        a1 = self.stack.pop() << 16

        a = a1 | a2 | a3
        b = b1 | b2 | b3

        if b == 0:
            raise ZeroDivisionError("QDIV div by zero error")
        else:
            c = int(a / b)
            self.stack.push(c >> 16)
            self.stack.push(c >> 8)
            self.stack.push(c & 0xFF)

            self.tick("TDIV")

    def hlt(self):
        raise Exception(f"HLT was raised on tick {self.ticks}")

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
            "JMPA": self.jmp_absolute,
            "JMPR": self.jmp_relative,
            "JZ": self.jz,
            "JL": self.jl,
            "JO": self.jo,
            "CALL": self.call,
            "RET": self.ret,
            "HLT": self.hlt,
            "FALSE": self.false,
            "TRUE": self.true,
            "CMP": self.cmp,
            "PRINT": self.print,
            "READ": self.read,
            "TMOD": self.tmod,
            "TDIV": self.tdiv
        }

        if opcode not in opcode_mapping:
            raise ValueError(f"Invalid opcode: {opcode}")

        # Call the corresponding method based on the opcode
        opcode_mapping[opcode]()


class Simulation:
    def __init__(self):
        self.cu = ControlUnit()
        self.cu.input_buffer = []
        self.cu.output_buffer = []

        self.cu.pc = 0x00C0
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


def configure_logger(logging_level):
    # Set the logging level for the root logger
    logging.basicConfig(level=logging_level, handlers=[])

    log_folder = 'log/model'
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder)

    # Set the maximum log file size
    log_file_max_size = 50 * 1024 * 1024  # 50 MB

    # Create a rotating file handler
    file_handler = RotatingFileHandler(os.path.join(log_folder, 'model.log'), maxBytes=log_file_max_size,
                                       backupCount=999)
    file_handler.setLevel(logging_level)

    # Create a formatter and add it to the file handler
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)


def main(program_filepath, input_filepath, logging_level):
    configure_logger(logging_level)

    with open(input_filepath, encoding="utf-8") as input_file:
        with open(program_filepath, encoding="utf-8") as program_file:
            program = json.loads(program_file.read())

            simulation = Simulation()
            simulation.cu.imem.init_data(program["instructions"])
            simulation.cu.ram.data = program["data"]

            input_file_string = input_file.read()
            for character in input_file_string:
                simulation.cu.input_buffer.append(ord(character))
            simulation.cu.input_buffer.reverse()
            simulation.cu.input_buffer.append(len(simulation.cu.input_buffer))

            try:
                logging.log(logging.INFO, f'Original input: "{input_file_string}"')
                logging.info("Reversed input buffer:")
                for index, character in enumerate(simulation.cu.input_buffer):
                    logging.log(logging.INFO, f"    {index}: {character}")
                logging.log(logging.INFO, ']')

                logging.info("\nNot void imem:")
                for i, instr in enumerate(simulation.cu.imem.data):
                    if instr["value"] != 0:
                        try:
                            int(instr["value"])
                            logging.info(f'0x{i:04X} | 0x{instr["value"]:04X}')
                        except ValueError:
                            logging.info(f'0x{i:04X} | {instr["value"]}')

                start_time = time.time()
                logging.log(logging.INFO, f"\n=== Simulation start ===")
                simulation.simulate()
            except Exception as e:
                logging.log(logging.INFO, e)
                logging.log(logging.INFO,
                            f"=== Simulation end. Ticks: {simulation.cu.ticks}. Time elapsed: {time.time() - start_time:.6f}s ===")

                logging.log(logging.INFO, "\nStack printed:")
                simulation.cu.stack.print_stack()

                logging.log(logging.INFO, "\nOutput buffer: [")
                for index, character in enumerate(simulation.cu.output_buffer):
                    logging.log(logging.INFO, f"    {index}: {character}")
                logging.log(logging.INFO, ']')
                logging.log(logging.INFO, f'Output buffer jointed: "{''.join(simulation.cu.output_buffer)}"')


if __name__ == '__main__':
    source_code_path_arg = sys.argv[1]
    input_filepath_arg = sys.argv[2]
    logging_level_arg = sys.argv[3]

    model_debug_leve = logging.debug if logging_level_arg != "info" else logging.INFO

    main(source_code_path_arg, input_filepath_arg, model_debug_leve)
