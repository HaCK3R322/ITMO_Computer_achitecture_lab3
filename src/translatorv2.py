import json
import logging
import os
import re
import shutil
from logging.handlers import RotatingFileHandler
from typing import List
from typing import Tuple


class AddressTable:
    def __init__(self, size, start_address, name, logger):
        self.data: List[int] = [0] * (size * 2)
        self.max_size: int = size
        self.reserved_count: int = 0
        self.start_address: int = start_address
        self.name = name
        self.logger = logger

    def reserve(self) -> int:
        assert self.reserved_count < self.max_size, f'CANT GET MORE TO ADDRESS TABLE OF {self.start_address:04X}'
        reserved_offset = self.reserved_count
        self.reserved_count += 1
        return reserved_offset

    def write_to_offset(self, offset, value):
        self.logger.info(
            f"Writing to table {self.name} offset {offset}: imem[{self.start_address + offset * 2:04X}] = {(value >> 8) & 0xFF:02X}")
        self.data[offset * 2] = (value >> 8) & 0xFF
        self.logger.info(
            f"Writing to table {self.name} offset {offset}: imem[{self.start_address + offset * 2 + 1:04X}] = {value & 0xFF:02X}")
        self.data[offset * 2 + 1] = value & 0xFF

    def print(self):
        self.logger.info('----------------')
        for index, value in enumerate(self.data):
            self.logger.info(f'| 0x{index:04X} | {self.data[index]:02x} |')
        self.logger.info('----------------')

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
        self.jmpa_instructions_and_reserved_offset_and_relative_shift: List[Tuple[Instruction, int, int]] = []

    def add_instruction(self, instruction):
        self.instructions.append(instruction)
        self.instructions_counter += 1


class Variable:
    def __init__(self, name, address, variable_index):
        self.name = name
        self.address = address
        self.index = variable_index


class Translator:
    def __init__(self, sourcecode, logger=None):
        self.logger = logger if logger is not None else configure_logger(logging_level=logging.INFO, logger_name="default_logger")

        self.source: str = sourcecode
        self.current_token = None
        self.current_token_index = -1

        self.load = AddressTable(32, 0x0000, "LOAD table", self.logger)
        self.call = AddressTable(32, 0x0040, "CALL table", self.logger)
        self.jmp = AddressTable(32, 0x0080, "JMPA table", self.logger)

        self.instructions: List[Instruction] = []
        self.instruction_counter = 0

        self.functions: List[Function] = []
        self.currently_defining_function_with_name = None

        self.recursion_level_if = 0
        self.labels: List[Tuple[int, int]] = []
        self.begin_last_label_stack: List[int] = [-1]

        self.data: List[int] = [0] * 0x10000
        self.START_ADDRESS_OF_ADDRESSES = 0x07f6
        self.CONSTANTS_START_ADDRESS = 0x0800
        self.TCONSTANTS_START_ADDRESS = 0x0900
        self.VARIABLES_ADDRESSES_ADDRESS = 0x0c00
        self.VARIABLES_VALUES_ADDRESS = 0x0e00
        self.STRINGS_ADDRESS = 0x1100
        self.init_addresses_in_data()
        self.init_load()

        self.variables: List[Variable] = []
        self.number_of_constants = 0
        self.number_of_tconstants = 0
        self.number_of_strings = 0

    def translate(self):
        self.drop_out_comments_from_source_code()
        tokens: List[str] = self.tokenize()
        self.logger.info(f"tokenized: {tokens}")

        for i, token in enumerate(tokens):
            if token[0] != '"':
                token = token.upper()

            self.current_token = token
            self.current_token_index = i

            if len(self.variables) > 0 and self.variables[-1].name is None:
                variable_name = token
                if self.is_name_valid(variable_name):
                    if self.currently_defining_function_with_name is not None:
                        variable_name = self.currently_defining_function_with_name + "." + variable_name

                    self.logger.info(
                        f"Assigning to variable with address 0x{self.variables[-1].address:04X} name {variable_name}")
                    self.variables[-1].name = variable_name
                else:
                    raise SyntaxError(f"Variable with name {variable_name} already defined or clashes with reserved word")

            elif token == "+":
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
                self.append(token)

            elif token == '!':
                self.append("SET")
            elif token == '@':
                self.append("GET")

            elif token == '.':
                self.append("PRINT")
            elif token == 'READ':
                self.append("READ")

            elif token[0] == ':':
                function_name = token[1:]
                if self.get_function_by_name(function_name) is not None:
                    raise SyntaxError(f"function with name {function_name} already defined!")

                if self.currently_defining_function_with_name is not None:
                    raise SyntaxError(
                        f"Cant define functions inside functions. Currently defining: {self.currently_defining_function_with_name}")

                # TODO: check namings
                self.reserve_function(function_name)
                self.currently_defining_function_with_name = function_name
            elif token == ';':
                self.currently_defining_function_with_name = None

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
                    self.process_until_for_regular()
                else:
                    func = self.get_function_by_name(self.currently_defining_function_with_name)
                    self.preprocess_until_for_functions(func)

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
                        self.push_constant_on_top(token_digit)

                    elif -8388608 <= token_digit <= 8388607:
                        self.logger.info(
                            f'WARNING: casting token {token} to TRIPLE-LENGTH INT, it will take 3 top-stack values and uses 3 LOAD cells')
                        if token_digit < 0:
                            token_digit += 0x1000000
                        self.push_tconstant_on_top(token_digit)

            elif len(token) == 4 and token[0] == "0" and token[1] == "X":
                hex_digits = token[2:]
                decimal_value = int(hex_digits, 16)
                self.push_constant_on_top(decimal_value)

            elif token == "TRUE":
                self.append("TRUE")

            elif token == "FALSE":
                self.append("FALSE")

            elif token == "T+":
                self.append_tsum_instructions()

            elif token == "T!":
                self.append_tset_instructions()

            elif token == "T@":
                self.append_tget_instructions()

            elif token == "T=":
                self.append_tequals_instructions()

            elif token == 'TDUP':
                self.append_tdup_instructions()

            elif token == "T%":
                self.append("TMOD")

            elif token == "T/":
                self.append("TDIV")

            elif token[0] == "\"":
                self.push_string_address_on_top(token)

            elif token == 'VARIABLE':
                variable = Variable(
                    None,
                    self.VARIABLES_VALUES_ADDRESS,
                    len(self.variables)
                )
                self.data[self.VARIABLES_ADDRESSES_ADDRESS] = variable.address >> 8
                self.data[self.VARIABLES_ADDRESSES_ADDRESS + 1] = variable.address & 0xFF

                self.variables.append(variable)

                self.VARIABLES_VALUES_ADDRESS += 1
                self.VARIABLES_ADDRESSES_ADDRESS += 2

            elif token == 'TVARIABLE':
                variable = Variable(
                    None,
                    self.VARIABLES_VALUES_ADDRESS,
                    len(self.variables)
                )

                self.data[self.VARIABLES_ADDRESSES_ADDRESS] = variable.address >> 8
                self.data[self.VARIABLES_ADDRESSES_ADDRESS + 1] = variable.address & 0xFF
                self.variables.append(variable)

                self.VARIABLES_VALUES_ADDRESS += 3
                self.VARIABLES_ADDRESSES_ADDRESS += 2

            elif self.get_variable_by_name(token) is not None:
                variables_addresses_offset_index = 4
                self.append("LOAD", offset=variables_addresses_offset_index)
                self.append("LOAD", offset=variables_addresses_offset_index + 1)

                variable = self.get_variable_by_name(token)
                for i in range(variable.index):
                    self.append("INC")
                    self.append("INC")

                self.append("OVER")
                self.append("OVER")
                self.append("INC")
                self.append("GET")
                self.append("ROT")
                self.append("ROT")
                self.append("GET")
                self.append("SWAP")

            elif self.get_function_by_name(token) is not None:
                func = self.get_function_by_name(token)
                self.append("CALL", offset=func.call_offset)

            else:
                raise SyntaxError(f'Unknown token [{token}]')

        self.add_instruction(Instruction("HLT", -1))

        self.process_if_statements_for_regular()

        self.define_functions()
        self.postprocess_shift_functions_jmpa()
        self.process_if_statements_for_functions()

        self.merge_address_tables()

        return self.instructions, self.data

    def init_addresses_in_data(self):
        self.data[self.START_ADDRESS_OF_ADDRESSES + 0] = self.CONSTANTS_START_ADDRESS >> 8
        self.data[self.START_ADDRESS_OF_ADDRESSES + 1] = self.CONSTANTS_START_ADDRESS & 0xFF
        self.data[self.START_ADDRESS_OF_ADDRESSES + 2] = self.TCONSTANTS_START_ADDRESS >> 8
        self.data[self.START_ADDRESS_OF_ADDRESSES + 3] = self.TCONSTANTS_START_ADDRESS & 0xFF
        self.data[self.START_ADDRESS_OF_ADDRESSES + 4] = self.VARIABLES_ADDRESSES_ADDRESS >> 8
        self.data[self.START_ADDRESS_OF_ADDRESSES + 5] = self.VARIABLES_ADDRESSES_ADDRESS & 0xFF
        self.data[self.START_ADDRESS_OF_ADDRESSES + 6] = self.VARIABLES_VALUES_ADDRESS >> 8
        self.data[self.START_ADDRESS_OF_ADDRESSES + 7] = self.VARIABLES_VALUES_ADDRESS & 0xFF
        self.data[self.START_ADDRESS_OF_ADDRESSES + 8] = self.STRINGS_ADDRESS >> 8
        self.data[self.START_ADDRESS_OF_ADDRESSES + 9] = self.STRINGS_ADDRESS & 0xFF

    def init_load(self):
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 0)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 1)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 2)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 3)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 4)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 5)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 6)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 7)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 8)
        self.load.write_to_offset(self.load.reserve(), self.START_ADDRESS_OF_ADDRESSES + 9)

    def drop_out_comments_from_source_code(self):
        lines = self.source.split('\n')
        cleaned_lines = [line.split('#')[0] for line in lines]
        cleaned_code = '\n'.join(cleaned_lines)
        self.source = cleaned_code

    def tokenize(self) -> List[str]:
        pattern = r'(\s+|"[^"]+")'

        result = re.split(pattern, self.source)
        result = [item for item in result if item.strip() != '' and item != '\n']
        for i, token in enumerate(result):
            if token[0] != '"':
                result[i] = token.upper()

        return result

    def convert_instructions_to_list(self):
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

    def get_function_by_name(self, name):
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def add_instruction(self, instruction):
        if self.currently_defining_function_with_name is None:
            self.logger.info(f"Appending instruction {instruction.value}")
            self.instructions.append(instruction)
            self.instruction_counter += 1
        else:
            self.logger.info(
                f"Appending instruction {instruction.value} (function {self.currently_defining_function_with_name}) (token \'{self.current_token}\')")
            function = self.get_function_by_name(self.currently_defining_function_with_name)
            function.add_instruction(instruction)

    def append(self, instruction_name, offset=None):
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

    def get_address_tables_size(self):
        return self.load.max_size * 2 + self.call.max_size * 2 + self.jmp.max_size * 2

    def process_if_statements_for_regular(self):
        sorted_labels = sorted(self.labels, key=lambda pair: (pair[0], pair[1]))

        for instr in self.instructions:
            if instr.value == "JMPA" and len(sorted_labels) > 0:
                reserved_offset = self.jmp.reserve()
                relative_jmp_address = sorted_labels.pop(0)[1]  # ~ instruction counter
                shift = self.get_address_tables_size()
                jmp_address = relative_jmp_address + shift
                self.jmp.write_to_offset(reserved_offset, jmp_address)

                instr.offset = reserved_offset

    def process_if_statements_for_functions(self):
        for func in self.functions:
            sorted_labels = sorted(func.labels, key=lambda pair: (pair[0], pair[1]))

            for instr in func.instructions:
                if instr.value == "JMPA" and instr.offset == -1:
                    assert func.start_address != -1, f'FUNC START ADDRESS {func.start_address}'

                    try:
                        reserved_offset = self.jmp.reserve()
                        relative_jmp_address = sorted_labels.pop(0)[1]  # ~ instruction counter
                        shift = func.start_address
                        jmp_address = relative_jmp_address + shift

                        self.jmp.write_to_offset(reserved_offset, jmp_address)

                        instr.offset = reserved_offset
                    except IndexError:
                        raise SyntaxError(f'Run out of labels during processing IF statement inside function {func.name}. Maybe forgot THEN after some IF?')

    def process_until_for_regular(self):
        self.logger.info("Processing UNTIL token outside of any function")
        number_of_added_instructions = self.instruction_counter - self.begin_last_label_stack.pop()

        shift = self.get_address_tables_size()
        address_to_jmp = self.instruction_counter - number_of_added_instructions - 1 + shift

        reserved_offset_jmp = self.jmp.reserve()
        self.jmp.write_to_offset(reserved_offset_jmp, address_to_jmp)

        self.append("FALSE")
        self.append("CMP")
        self.append("DROP")
        self.append("DROP")
        self.append("JZ", offset=1)
        self.append("JMPR", offset=1)
        self.append("JMPA", offset=reserved_offset_jmp)

    def preprocess_until_for_functions(self, func: Function):
        self.logger.info(f"Pre-processing UNTIL token inside of function {func.name}: ")
        number_of_added_instructions = func.instructions_counter - func.begin_last_label_stack.pop()

        address_to_jmp_relative = func.instructions_counter - number_of_added_instructions - 1
        self.logger.info(f"     relative JMPA address = {address_to_jmp_relative} (0x{address_to_jmp_relative:04X})")

        reserved_jmp_offset = self.jmp.reserve()

        self.append("FALSE")
        self.append("CMP")
        self.append("DROP")
        self.append("DROP")
        self.append("JZ", offset=1)
        self.append("JMPR", offset=1)
        self.append("JMPA", offset=reserved_jmp_offset)

        func.jmpa_instructions_and_reserved_offset_and_relative_shift.append(
            (func.instructions[-1], reserved_jmp_offset, address_to_jmp_relative))

    def postprocess_shift_functions_jmpa(self):
        for func in self.functions:
            self.logger.info(f"Post-processing UNTIL token inside of function {func.name}: ")
            for instr_and_shift in func.jmpa_instructions_and_reserved_offset_and_relative_shift:
                jmpa_instruction = instr_and_shift[0]
                address_to_jmp_relative = instr_and_shift[2]
                new_jmpa_instruction_offset = func.start_address + address_to_jmp_relative

                self.logger.info(f'    absolute JMPA: address = {new_jmpa_instruction_offset:04x}')

                reserved_jmpa_offset = instr_and_shift[1]
                self.jmp.write_to_offset(reserved_jmpa_offset, new_jmpa_instruction_offset)

    def define_functions(self):
        for func in self.functions:
            # add to each function RET
            self.logger.info(f"Appending instruction RET (function {func.name})")
            func.add_instruction(Instruction("RET", -1))

            # add all instructions of function
            function_start = self.instruction_counter + self.get_address_tables_size()
            self.logger.info(
                f"Function {func.name} assigned start: {function_start:04X} = {self.instruction_counter} + {self.get_address_tables_size()} -> 0x{function_start - 1:02X}")
            func.start_address = function_start
            for instruction in func.instructions:
                self.instruction_counter += 1
                self.instructions.append(instruction)

            # save to call table addresses of func start
            self.call.write_to_offset(func.call_offset, function_start - 1)

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

    def append_tset_instructions(self):
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

    def append_tget_instructions(self):
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

    def append_tequals_instructions(self):
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

    def append_tdup_instructions(self):
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

    def push_string_address_on_top(self, token):
        string = token[1:-1]
        string_length = len(string)

        if string_length > 255:
            raise SyntaxError(
                f"string too big ({string_length} is more than 255 symbols limit). String: {string}")

        string_start_address = self.STRINGS_ADDRESS
        self.data[self.STRINGS_ADDRESS] = string_length
        self.STRINGS_ADDRESS += 1

        for character in string:
            ascii_code = ord(character)
            self.data[self.STRINGS_ADDRESS] = ascii_code
            self.STRINGS_ADDRESS += 1

        string_start_address_h = string_start_address >> 8
        string_start_address_l = string_start_address & 0xFF

        self.push_constant_on_top(string_start_address_h)
        self.push_constant_on_top(string_start_address_l)

    def push_constant_on_top(self, constant):
        if not 0 <= constant <= 255:
            raise ValueError(f"Unsigned constant {constant} out of bounds [0; 255]!")

        self.data[self.CONSTANTS_START_ADDRESS] = constant
        self.logger.info(f'self.data[{self.CONSTANTS_START_ADDRESS:04X}] = {constant:02X}')
        self.append("LOAD", offset=0)
        self.append("LOAD", offset=1)

        for i in range(self.number_of_constants):
            self.append("INC")

        self.append("GET")

        self.CONSTANTS_START_ADDRESS += 1
        self.number_of_constants += 1

    def push_tconstant_on_top(self, constant):
        if not 0 <= constant <= 16777216:
            raise ValueError(f"Unsigned tconstant {constant} out of bounds [0; 16777216]!")

        constant_high = constant >> 16
        constant_mid = (constant >> 8) & 0xFF
        constant_low = constant & 0xFF

        self.data[self.TCONSTANTS_START_ADDRESS] = constant_high
        self.data[self.TCONSTANTS_START_ADDRESS + 1] = constant_mid
        self.data[self.TCONSTANTS_START_ADDRESS + 2] = constant_low
        self.logger.info(f'self.data[{self.TCONSTANTS_START_ADDRESS:04X}] = {constant_high:02X}')
        self.logger.info(f'self.data[{self.TCONSTANTS_START_ADDRESS + 1:04X}] = {constant_mid:02X}')
        self.logger.info(f'self.data[{self.TCONSTANTS_START_ADDRESS + 2:04X}] = {constant_low:02X}')
        self.append("LOAD", offset=2)
        self.append("LOAD", offset=3)

        for i in range(self.number_of_tconstants):
            self.append("INC")

        self.append("OVER")
        self.append("OVER")
        self.append("INC")
        self.append("GET")
        self.append("ROT")
        self.append("ROT")
        self.append("OVER")
        self.append("OVER")
        self.append("INC")
        self.append("INC")
        self.append("GET")
        self.append("ROT")
        self.append("ROT")
        self.append("GET")
        self.append("ROT")
        self.append("ROT")

        self.CONSTANTS_START_ADDRESS += 1
        self.number_of_constants += 1

    def is_reserved_word(self, word):
        operators = ['+', '-', '/', '*', '%', '>', '<', '=', 'SWAP', 'DUP', 'DROP', 'OVER', 'ROT', '!', '@', '.',
                     'READ', ':function_name', ';', 'IF', 'THEN', 'BEGIN', 'UNTIL', 'VARIABLE']
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
            int(string)
            return True
        except ValueError:
            return False

    def get_variable_by_name(self, variable_name):
        if self.currently_defining_function_with_name is not None:
            variable_name = self.currently_defining_function_with_name + "." + variable_name

        for var in self.variables:
            if var.name == variable_name:
                return var
        return None

    def is_name_valid(self, name):
        if (self.get_variable_by_name(name) is not None
                or self.get_function_by_name(name is not None)):
            return False

        if name.isdigit():
            return False
        if name[0].isdigit():
            return False
        if self.is_reserved_word(name):
            return False

        return True


def configure_logger(logging_level, logger_name=None):
    if logger_name is None:
        logger_name = "default_translator_logger"

    configured_logger = logging.getLogger(logger_name)

    # Set the logging level for the root logger
    configured_logger.setLevel(logging_level)
    configured_logger.handlers = []

    log_folder = f'log/translator/{logger_name}'
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder)

    # Set the maximum log file size
    log_file_max_size = 50 * 1024 * 1024  # 50 MB

    logfile_path = os.path.join(log_folder, logger_name + '.log')
    # Create a rotating file handler
    file_handler = RotatingFileHandler(logfile_path, maxBytes=log_file_max_size,
                                       backupCount=999)
    file_handler.setLevel(logging_level)

    # Create a formatter and add it to the file handler
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the root logger
    configured_logger.handlers.append(file_handler)

    return configured_logger


def main(source_path, output_path, configured_logger=None):
    if configured_logger is None:
        configured_logger = configure_logger(logging_level=logging.INFO, logger_name='default_translator_logger')

    with open(source_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()

        configured_logger.info("SOURCE CODE:")
        configured_logger.info(source_code)

        configured_logger.info("\n===== translation start =====")
        translator = Translator(source_code, configured_logger)

        try:
            instructions, data = translator.translate()
            configured_logger.info("===== translation end =====\n")
            configured_logger.info(f"Total number of translated instructions: {len(translator.instructions) - 0x00C0}")

            program = {"instructions": translator.convert_instructions_to_list(), "data": data}

            with open(output_path, "w", encoding="utf-8") as bin_file:
                bin_file.write(json.dumps(program, indent=4))

        except SyntaxError as syntax_error:
            configured_logger.info(f'TRANSLATION SYNTAX ERROR: {syntax_error}')
            raise syntax_error

    configured_logger.handlers[0].flush()
    logging.shutdown()


if __name__ == '__main__':
    main("source.forth", "program.lab")
