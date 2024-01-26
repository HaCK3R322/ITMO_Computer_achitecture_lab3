import json
import logging
from typing import List
from typing import Tuple


class AddressTable:
    def __init__(self, size, start_address):
        self.data: List[int] = [0] * (size * 2)
        self.max_size: int = size
        self.reserved_count: int = 0
        self.start_address: int = start_address

    def reserve(self) -> int:
        assert self.reserved_count < self.max_size, f'CANT GET MORE TO ADDRESS TABLE OF {self.start_address:04X}'
        reserved_offset = self.reserved_count
        self.reserved_count += 1
        return reserved_offset

    def write_to_offset(self, offset, value):
        self.data[offset * 2] = (value >> 8) & 0xFF
        self.data[offset * 2 + 1] = value & 0xFF

    def print(self):
        print('----------------')
        for index, value in enumerate(self.data):
            print(f'| 0x{index:04X} | {self.data[index]:02x} |')
        print('----------------')

    def get_as_instructions_data(self):
        instructions_data = []
        for value in self.data:
            instructions_data.append(Instruction(value, -1, "initialization"))

        return instructions_data


class Instruction:
    def __init__(self, value, related_token_index: int, related_token: str = None, offset: int = None):
        self.value = value
        self.related_token_index: int = related_token_index
        self.related_token: str = related_token
        self.offset: int = offset


class Function:
    def __init__(self, name: str, call_offset: int):
        self.name: str = name
        self.call_offset: int = call_offset
        self.instructions: List[Instruction] = []
        self.instructions_counter: int = 0
        self.labels: List[Tuple[int, int]] = []
        self.recursion_level: int = 0
        self.start_address: int = -1
        self.begin_last_label_stack: List[int] = [-1]
        self.instructions_to_shift_jmpa: List[Instruction] = []

    def add_instruction(self, instruction):
        self.instructions.append(instruction)
        self.instructions_counter += 1


class Variable:
    def __init__(self, name,
                 reserved_offset1,
                 reserved_offset2,
                 real_address,
                 address_of_cell_with_real_address_h,
                 address_of_cell_with_real_address_l,
                 ):
        self.name = name

        self.reserved_offset1 = reserved_offset1
        self.reserved_offset2 = reserved_offset2

        self.real_address = real_address

        self.address_of_cell_with_real_address_h = address_of_cell_with_real_address_h
        self.address_of_cell_with_real_address_l = address_of_cell_with_real_address_l

class Variable2:
    def __init__(self, name, address, offset):
        self.name = name
        self.address = address
        self.offset = offset



class Translator:
    def __init__(self, sourcecode):
        self.source: str = sourcecode
        self.current_token = None
        self.current_token_index = -1

        self.load = AddressTable(32, 0x0000)
        self.call = AddressTable(32, 0x0040)
        self.jmp = AddressTable(32, 0x0080)

        self.instructions: List[Instruction] = []
        self.instruction_counter = 0

        self.functions: List[Function] = []
        self.currently_defining_function_with_name = None

        self.recursion_level_if = 0
        self.labels: List[Tuple[int, int]] = []

        self.begin_last_label_stack: List[int] = [-1]

        self.data: List[int] = [0] * 0x10000

        self.constants_pointer = 0x0800

        self.variables: List[Variable] = []
        self.variable_real_address_to_use = 0x0832
        self.variable_cell_address_to_real_address_H_to_use = 0x0864
        self.variable_cell_address_to_real_address_L_to_use = 0x0865

        self.variable_real_address_to_use = 0x0832
        self.variable_cell_address_to_real_address_H_to_use = 0x0864
        self.variable_cell_address_to_real_address_L_to_use = 0x0865

        self.str_real_address_to_use = 0x1000

    def drop_out_comments_from_source_code(self):
        lines = self.source.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('#')]
        cleaned_code = '\n'.join(cleaned_lines)
        self.source = cleaned_code

    def convert_instruction_to_list(self):
        instr_list = []
        for instr in self.instructions:
            instr_list.append({
                "value": instr.value,
                "related_token_index": instr.related_token_index,
                "related_token": instr.related_token,
                "offset": instr.offset
            })
        return instr_list

    def reserve_function(self, name):
        self.functions.append(Function(name, self.call.reserve()))

    def get_address_for_next_function_start(self):
        raise Exception("bad")

    def get_function_by_name(self, name):
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def add_instruction(self, instruction):
        if self.currently_defining_function_with_name is None:
            self.instructions.append(instruction)
            self.instruction_counter += 1
        else:
            function = self.get_function_by_name(self.currently_defining_function_with_name)
            function.add_instruction(instruction)

    def append(self, instruction_name, offset=None):
        logging.log(logging.INFO, f"Appending instruction {instruction_name}")
        instruction = Instruction(instruction_name,
                                  self.current_token_index,
                                  self.current_token,
                                  offset=offset)
        self.add_instruction(instruction)

    def add_label(self, recursion_level: int):
        if self.currently_defining_function_with_name is None:
            self.labels.append((recursion_level, self.instruction_counter - 1))
        else:
            function = self.get_function_by_name(self.currently_defining_function_with_name)
            function.labels.append((function.recursion_level, function.instructions_counter - 1))

    def recursion_level_if_inc(self):
        if self.currently_defining_function_with_name is None:
            self.recursion_level_if += 1
        else:
            function = self.get_function_by_name(self.currently_defining_function_with_name)
            function.recursion_level += 1

    def recursion_level_if_dec(self):
        if self.currently_defining_function_with_name is None:
            self.recursion_level_if -= 1
        else:
            function = self.get_function_by_name(self.currently_defining_function_with_name)
            function.recursion_level -= 1

    def merge_address_tables(self):
        self.instructions = (
                self.load.get_as_instructions_data()
                + self.call.get_as_instructions_data()
                + self.jmp.get_as_instructions_data()
                + self.instructions
        )

    def process_if_statements_for_regular(self):
        sorted_labels = sorted(self.labels, key=lambda pair: (pair[0], pair[1]))

        for instr in self.instructions:
            print(instr)
            if instr.value == "JMPA" and len(sorted_labels) > 0:
                reserved_offset = self.jmp.reserve()
                relative_jmp_address = sorted_labels.pop(0)[1]  # ~ instruction counter
                shift = (
                        len(self.load.get_as_instructions_data())
                        + len(self.call.get_as_instructions_data())
                        + len(self.jmp.get_as_instructions_data())
                )
                jmp_address = relative_jmp_address + shift

                self.jmp.write_to_offset(reserved_offset, jmp_address)

                instr.offset = reserved_offset

    def process_if_statements_for_functions(self):
        for func in self.functions:
            sorted_labels = sorted(func.labels, key=lambda pair: (pair[0], pair[1]))

            for instr in func.instructions:
                if instr.value == "JMPA" and instr.offset == -1:
                    assert func.start_address != -1, f'FUNC START ADDRESS {func.start_address}'

                    reserved_offset = self.jmp.reserve()
                    relative_jmp_address = sorted_labels.pop(0)[1]  # ~ instruction counter
                    shift = func.start_address
                    jmp_address = relative_jmp_address + shift

                    self.jmp.write_to_offset(reserved_offset, jmp_address)

                    instr.offset = reserved_offset

    def process_until_for_regular(self, token_index, token):
        number_of_added_instructions = self.instruction_counter - self.begin_last_label_stack.pop()

        shift = (
                len(self.load.get_as_instructions_data())
                + len(self.call.get_as_instructions_data())
                + len(self.jmp.get_as_instructions_data())
        )
        address_to_jmp = self.instruction_counter - number_of_added_instructions + shift - 1

        reserved_offset_jmp = self.jmp.reserve()
        self.jmp.write_to_offset(reserved_offset_jmp, address_to_jmp)

        self.append("FALSE")
        self.append("CMP")
        self.append("DROP")
        self.append("DROP")
        self.append("JZ", offset=1)
        self.append("JMPR", offset=1)
        self.append("JMPA", offset=reserved_offset_jmp)

    def process_until_for_functions(self, func: Function, token_index, token):
        number_of_added_instructions = func.instructions_counter - func.begin_last_label_stack.pop()

        shift = (
                len(self.load.get_as_instructions_data())
                + len(self.call.get_as_instructions_data())
                + len(self.jmp.get_as_instructions_data())
        )
        address_to_jmp = func.instructions_counter - number_of_added_instructions - 1

        reserved_offset_jmp = self.jmp.reserve()
        self.jmp.write_to_offset(reserved_offset_jmp, address_to_jmp)

        self.append("FALSE")
        self.append("CMP")
        self.append("DROP")
        self.append("DROP")
        self.append("JZ", offset=1)
        self.append("JMPR", offset=1)
        self.append("JMPA", offset=reserved_offset_jmp)

        func.instructions_to_shift_jmpa.append(func.instructions[-1])

    def shift_functions_jmpa(self):
        for func in self.functions:
            for instr in func.instructions_to_shift_jmpa:
                a = self.jmp.data[instr.offset]
                b = self.jmp.data[instr.offset + 1]
                c = a | b
                c += func.start_address
                print(f'{c:04x}')
                self.jmp.write_to_offset(instr.offset, c)

    def define_functions(self):
        for func in self.functions:
            # add to each function RET
            func.add_instruction(Instruction("RET", -1))

            # add all instructions of function
            function_start = self.instruction_counter + (
                    len(self.load.get_as_instructions_data())
                    + len(self.call.get_as_instructions_data())
                    + len(self.jmp.get_as_instructions_data())
            )
            func.start_address = function_start
            for instruction in func.instructions:
                self.instruction_counter += 1
                self.instructions.append(instruction)

            # save to call table addresses of func start
            print('xxxx', func.call_offset, function_start)
            self.call.write_to_offset(func.call_offset, function_start - 1)

    def translate(self):
        self.drop_out_comments_from_source_code()
        tokens: List[str] = self.source.split()

        for i, token in enumerate(tokens):
            token = token.upper()

            self.current_token = token
            self.current_token_index = i

            if token == "+":
                self.append("SUM")
            elif token == "-":
                self.append("SUB")
            elif token == "*":
                self.append("MUL")
            elif token == "/":
                self.append("DIV")
            elif token == "%":
                self.append("MOD")

            elif token == "=":
                self.append("CMP")
                self.append("JZ", offset=4)
                self.append("DROP")
                self.append("DROP")
                self.append("FALSE")
                self.append("JMPR", offset=3)
                self.append("DROP")
                self.append("DROP")
                self.append("TRUE")
            elif token == ">":
                self.append("CMP")
                self.append("JZ", offset=5)
                self.append("JL", offset=4)
                self.append("DROP")
                self.append("DROP")
                self.append("TRUE")
                self.append("JMPR", offset=3)
                self.append("DROP")
                self.append("DROP")
                self.append("FALSE")
            elif token == "<":
                self.append("CMP")
                self.append("JZ", offset=5)
                self.append("JL", offset=4)
                self.append("DROP")
                self.append("DROP")
                self.append("FALSE")
                self.append("JMPR", offset=3)
                self.append("DROP")
                self.append("DROP")
                self.append("TRUE ")

            elif token in ['SWAP', 'DUP', 'DROP', 'OVER', 'ROT']:
                self.add_instruction(Instruction(token, i, token))

            elif token == '!':
                self.append("SET")
            elif token == '@':
                self.append("GET")

            elif token == '.':
                self.append("PRINT")
            elif token == 'ACCEPT':
                self.append("READ")

            elif token[0] == ':':
                function_name = token[1:]
                if self.get_function_by_name(function_name) is not None:
                    raise NameError(f"function with name {function_name} already defined!")

                # TODO: check namings
                self.reserve_function(function_name)
                self.currently_defining_function_with_name = function_name
            elif token == ';':
                self.currently_defining_function_with_name = None

            elif self.get_function_by_name(token) is not None:
                func = self.get_function_by_name(token)
                self.append("CALL", offset=func.call_offset)

            elif token == 'IF':
                self.append("FALSE")
                self.append("CMP")
                self.append("DROP")
                self.append("DROP")
                self.append("JZ", offset=1)
                self.append("JMPR", offset=1)
                self.append("JMPA", offset=-1)

                self.recursion_level_if_inc()
            elif token == 'THEN':
                self.add_label(self.recursion_level_if)
                self.recursion_level_if_dec()

            elif token == 'BEGIN':
                if self.currently_defining_function_with_name is None:
                    self.begin_last_label_stack.append(self.instruction_counter)
                else:
                    func = self.get_function_by_name(self.currently_defining_function_with_name)
                    func.begin_last_label_stack.append(func.instructions_counter)
            elif token == 'UNTIL':
                if self.currently_defining_function_with_name is None:
                    self.process_until_for_regular(i, token)
                else:
                    func = self.get_function_by_name(self.currently_defining_function_with_name)
                    self.process_until_for_functions(func, i, token)

            elif self.is_integer(token):
                token_digit: int = int(token)

                # instead of wasting LOAD better to use FALSE instruction because it's same result
                if token_digit == 0:
                    self.append("FALSE")
                elif token_digit == 1:
                    self.append("FALSE")
                    self.append("INC")
                else:
                    if -128 <= token_digit <= 127:
                        if token_digit < 0:
                            token_digit += 256
                        self.push_constant_on_top_instructions(token_digit, token, i)

                    elif -8388608 <= token_digit <= 8388607:
                        print(
                            f'WARNING: casting token {token} to TRIPLE-LENGTH INT, it will take 3 top-stack values and uses 3 LOAD cells')
                        if token_digit < 0:
                            token_digit += 0x1000000
                        constant_high = token_digit >> 16
                        constant_mid = (token_digit >> 8) & 0xFF
                        constant_low = token_digit & 0xFF
                        self.push_constant_on_top_instructions(constant_high, token, i)
                        self.push_constant_on_top_instructions(constant_mid, token, i)
                        self.push_constant_on_top_instructions(constant_low, token, i)

            elif len(token) == 4 and token[0] == "0" and token[1] == "X":
                hex_digits = token[2:]
                decimal_value = int(hex_digits, 16)
                self.push_constant_on_top_instructions(decimal_value, token, i)

            elif token == 'VARIABLE':
                reserved_offset1 = self.load.reserve()  # address to first part of variable address
                reserved_offset2 = self.load.reserve()  # address to first part of variable address

                variable = Variable(
                    None,
                    reserved_offset1,
                    reserved_offset2,
                    self.variable_real_address_to_use,
                    self.variable_cell_address_to_real_address_H_to_use,
                    self.variable_cell_address_to_real_address_L_to_use
                )

                self.data[variable.real_address] = 0
                self.data[variable.address_of_cell_with_real_address_h] = variable.real_address >> 8
                self.data[variable.address_of_cell_with_real_address_l] = variable.real_address & 0xFF

                self.load.write_to_offset(variable.reserved_offset1, variable.address_of_cell_with_real_address_h)
                self.load.write_to_offset(variable.reserved_offset2, variable.address_of_cell_with_real_address_l)

                self.variables.append(variable)

                self.variable_real_address_to_use += 1
                self.variable_cell_address_to_real_address_H_to_use += 1
                self.variable_cell_address_to_real_address_L_to_use += 1

            elif token == 'TVARIABLE':
                reserved_offset1 = self.load.reserve()  # address to first part of variable address
                reserved_offset2 = self.load.reserve()  # address to first part of variable address

                variable = Variable(
                    None,
                    reserved_offset1,
                    reserved_offset2,
                    self.variable_real_address_to_use,
                    self.variable_cell_address_to_real_address_H_to_use,
                    self.variable_cell_address_to_real_address_L_to_use
                )

                self.data[variable.real_address] = 0
                self.data[variable.address_of_cell_with_real_address_h] = variable.real_address >> 8
                self.data[variable.address_of_cell_with_real_address_l] = variable.real_address & 0xFF

                self.load.write_to_offset(variable.reserved_offset1, variable.address_of_cell_with_real_address_h)
                self.load.write_to_offset(variable.reserved_offset2, variable.address_of_cell_with_real_address_l)

                self.variables.append(variable)

                self.variable_real_address_to_use += 3
                self.variable_cell_address_to_real_address_H_to_use = self.variable_real_address_to_use >> 8
                self.variable_cell_address_to_real_address_L_to_use = self.variable_real_address_to_use & 0xFF

            elif token == "TRUE":
                self.append("TRUE")

            elif token == "FALSE":
                self.append("FALSE")

            elif token == "T+":
                self.append_tsum_instructions()

            elif token == "T!":
                self.append("OVER")
                self.append("OVER")
                self.append("TOR")
                self.append("TOR")
                self.append("OVER")
                self.append("OVER")
                self.append("TOR")
                self.append("TOR")
                self.append("OVER")
                self.append("OVER")
                self.append("TOR")
                self.append("TOR")

                self.append("FALSE")
                self.append("ROT")
                self.append("ROT")
                self.append("FALSE")
                self.append("FALSE")
                self.append("FALSE")
                self.append("INC")
                self.append("INC")
                # t+
                self.append_tsum_instructions()
                self.append("ROT")
                self.append("DROP")

                self.append("SET")

                self.append("RFROM")
                self.append("RFROM")

                self.append("FALSE")
                self.append("ROT")
                self.append("ROT")
                self.append("FALSE")
                self.append("FALSE")
                self.append("FALSE")
                self.append("INC")
                # t+
                self.append_tsum_instructions()

                self.append("ROT")
                self.append("DROP")
                self.append("SET")

                self.append("RFROM")
                self.append("RFROM")
                self.append("SET")

                self.append("RFROM")
                self.append("RFROM")
                self.append("DROP")
                self.append("DROP")

            elif token == "T@":
                self.append("OVER")
                self.append("OVER")
                self.append("TOR")
                self.append("TOR")
                self.append("OVER")
                self.append("OVER")
                self.append("TOR")
                self.append("TOR")

                self.append("GET")
                self.append("RFROM")
                self.append("RFROM")

                self.append("FALSE")
                self.append("ROT")
                self.append("ROT")
                self.append("FALSE")
                self.append("FALSE")
                self.append("FALSE")

                self.append("INC")
                # t+
                self.append_tsum_instructions()

                self.append("GET")
                self.append("RFROM")
                self.append("RFROM")

                self.append("FALSE")
                self.append("ROT")
                self.append("ROT")
                self.append("FALSE")
                self.append("FALSE")
                self.append("FALSE")

                self.append("INC")
                self.append("INC")
                # t+
                self.append_tsum_instructions()

                self.append("GET")

                self.append("SWAP")
                self.append("DROP")
                self.append("ROT")
                self.append("DROP")

            elif token == "T=":
                self.append("ROT")
                self.append("TOR")
                self.append("SWAP")
                self.append("TOR")
                self.append("CMP")
                self.append("JZ", offset=1)
                self.append("JMPR", offset=12)
                self.append("DROP")
                self.append("DROP")
                self.append("RFROM")
                self.append("CMP")
                self.append("JZ", offset=1)
                self.append("JMPR", offset=15)
                self.append("DROP")
                self.append("DROP")
                self.append("RFROM")
                self.append("CMP")
                self.append("JZ", offset=19)
                self.append("JMPR", offset=15)
                self.append("RFROM")
                self.append("RFROM")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("JMPR", offset=13)
                self.append("RFROM")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("DROP")
                self.append("JMPR", offset=7)
                self.append("DROP")
                self.append("DROP")
                self.append("JMPR", offset=4)
                self.append("DROP")
                self.append("DROP")
                self.append("TRUE")
                self.append("JMPR", offset=1)
                self.append("FALSE")

            elif token == 'TDUP':
                self.append("DUP")
                self.append("TOR")
                self.append("ROT")
                self.append("ROT")
                self.append("DUP")
                self.append("TOR")
                self.append("SWAP")
                self.append("DUP")
                self.append("TOR")
                self.append("SWAP")
                self.append("ROT")
                self.append("RFROM")
                self.append("RFROM")
                self.append("RFROM")

            elif token == "T%":
                self.append("TMOD")

            elif token == "T/":
                self.append("TDIV")

            elif len(self.variables) > 0 and self.variables[-1].name is None:
                variable_name = token
                if self.is_okay_variable_name(variable_name):
                    self.variables[-1].name = variable_name

            elif token[0] == "\"":
                string = token[1:]
                string_length = len(string)

                if string_length > 255:
                    raise SyntaxError(
                        f"string too big ({string_length} is more than 255 symbols limit). String: {string}")

                string_start = self.str_real_address_to_use
                self.str_real_address_to_use += 2

                self.data[string_start] = (string_start + 2) >> 8
                self.data[string_start + 1] = (string_start + 2) & 0xFF

                self.data[self.str_real_address_to_use] = string_length
                self.str_real_address_to_use += 1
                for character in string:
                    ascii_code = ord(character)
                    self.data[self.str_real_address_to_use] = ascii_code
                    self.str_real_address_to_use += 1

                offset1 = self.load.reserve()
                offset2 = self.load.reserve()

                self.load.write_to_offset(offset1, string_start)
                self.load.write_to_offset(offset2, string_start + 1)

                self.append("LOAD", offset=offset1)
                self.append("LOAD", offset=offset2)


            elif self.get_variable_by_name(token) is not None:
                variable = self.get_variable_by_name(token)
                self.append("LOAD", offset=variable.reserved_offset1)
                self.append("LOAD", offset=variable.reserved_offset2)


            else:
                raise ValueError(f'Unknown token {token}')

        self.add_instruction(Instruction("HLT", -1))

        self.process_if_statements_for_regular()

        self.define_functions()
        self.shift_functions_jmpa()
        self.process_if_statements_for_functions()

        self.merge_address_tables()

        # print("LOAD address table values:")
        # self.load.print()
        # print("CALL address table values:")
        # self.call.print()
        # print("JMP address table values:")
        # self.jmp.print()

        return self.instructions, self.data

    def append_tsum_instructions(self):
        self.append("ROT")
        self.append("TOR")
        self.append("SWAP")
        self.append("TOR")
        self.append("SUM")
        self.append("JO", 1)
        self.append("JMPR", 9)
        self.append("SWAP")
        self.append("INC")
        self.append("SWAP")
        self.append("JO", 1)
        self.append("JMPR", 4)
        self.append("ROT")
        self.append("INC")
        self.append("ROT")
        self.append("ROT")

        self.append("ROT")
        self.append("ROT")
        self.append("RFROM")
        self.append("SUM")
        self.append("JO", 1)
        self.append("JMPR", 3)
        self.append("SWAP")
        self.append("INC")
        self.append("SWAP")

        self.append("SWAP")
        self.append("RFROM")
        self.append("SUM")
        self.append("ROT")
        self.append("ROT")
        self.append("SWAP")

    def push_constant_on_top_instructions(self, constant, token, i):
        constant_data_address = self.constants_pointer
        self.constants_pointer += 1
        reserved_offset = self.load.reserve()
        self.load.write_to_offset(reserved_offset, constant_data_address)
        if not 0 <= constant <= 255:
            raise ValueError(f"Unsigned constant {constant} token index:token={i}:{token} out of bounds [0; 255]!")
        self.data[constant_data_address] = constant
        self.append("LOAD", offset=reserved_offset)

    def is_reserved_word(self, word):
        operators = ['+', '-', '/', '*', '%', '>', '<', '=', 'SWAP', 'DUP', 'DROP', 'OVER', 'ROT', '!', '@', '.',
                     'ACCEPT', ':function_name', ';', 'IF', 'THEN', 'BEGIN', 'UNTIL', 'VARIABLE']
        return word in operators

    def int_to_eight_bit(self, value):
        """
        transform value
        :param value:
        :return:
        """
        if value < 0:
            # Используем побитовое "И" с 0xFF для получения 8 бит
            result = 0xFF & (256 + value)
        else:
            result = value

        return result

    def is_integer(self, string):
        try:
            int_value = int(string)
            return True
        except ValueError:
            return False

    def get_variable_by_name(self, variable_name):
        for var in self.variables:
            if var.name == variable_name:
                return var
        return None

    def is_okay_variable_name(self, variable_name):
        for var in self.variables:
            if var.name == variable_name:
                return False
        if variable_name.isdigit():
            return False
        if variable_name[0].isdigit():
            return False
        return not self.is_reserved_word(variable_name)


def main(source_path, output_path):
    with open(source_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()

        print("SOURCE CODE:")
        print(source_code)

        print("\n===== translation start =====")
        translator = Translator(source_code)
        instructions, data = translator.translate()
        print("===== translation end =====\n")

        program = {"instructions": translator.convert_instruction_to_list(), "data": data}
        print("\nTranslated code:")

        with open(output_path, "w", encoding="utf-8") as bin_file:
            bin_file.write(json.dumps(program, indent=4))


if __name__ == '__main__':
    main("inputcode.txt", "outputcode.txt")
