import json
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
            instructions_data.append({"value": value, "related_token_index": -1})

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

    def add_instruction(self, instruction):
        self.instructions.append(instruction)
        self.instructions_counter += 1


class Translator:
    def __init__(self, sourcecode):
        self.tokens = sourcecode.split()

        self.load = AddressTable(32, 0x0000)
        self.call = AddressTable(32, 0x0040)
        self.jmp = AddressTable(32, 0x0080)

        self.instructions: List[Instruction] = []
        self.instruction_counter = 0

        self.functions: List[Function] = []
        self.currently_defining_function_with_name = None

        self.recursion_level_if = 0
        self.labels: List[Tuple[int, int]] = []

        self.data = []

    @staticmethod
    def convert_to_instruction(value, related_token_index, token=None, offset=None):
        if offset is not None:
            return Instruction(value, related_token_index, related_token=token, offset=offset)
        else:
            return {
                "value": value,
                "related_token_index": related_token_index + 1,
                "related_token": token
            }

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

    # вызывается после добавления в основной список всех инструкций
    def define_functions(self):
        for func in self.functions:
            # add to each function RET
            func.add_instruction(Instruction("RET", -1))

            # add all instructions of function
            function_start = self.instruction_counter
            for instruction in func.instructions:
                self.instruction_counter += 1
                self.instructions.append(instruction)

            # save to call table addresses of func start
            self.call.write_to_offset(func.call_offset, function_start)

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
            if instr.value == "JMPA":
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
        sorted_labels = sorted(self.labels, key=lambda pair: (pair[0], pair[1]))

        for instr in self.instructions:
            if instr.value == "JMPA":
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

    def translate(self):
        for i, token in enumerate(self.tokens):
            token = token.upper()

            if token == "+":
                self.add_instruction(Instruction("SUM", i, token))
            elif token == "-":
                self.add_instruction(Instruction("SUB", i, token))
            elif token == "*":
                self.add_instruction(Instruction("MUL", i, token))
            elif token == "/":
                self.add_instruction(Instruction("DIV", i, token))
            elif token == "%":
                self.add_instruction(Instruction("MOD", i, token))

            elif token == "=":
                self.add_instruction(Instruction("CMP", i, token))
                self.add_instruction(Instruction("JZ", i, token, offset=4))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("FALSE", i, token))
                self.add_instruction(Instruction("JMPR", i, token, offset=3))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("TRUE", i, token))
            elif token == ">":
                self.add_instruction(Instruction("CMP", i, token))
                self.add_instruction(Instruction("JZ", i, token, offset=5))
                self.add_instruction(Instruction("JL", i, token, offset=4))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("TRUE", i, token))
                self.add_instruction(Instruction("JMPR", i, token, offset=3))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("FALSE", i, token))
            elif token == "<":
                self.add_instruction(Instruction("CMP", i, token))
                self.add_instruction(Instruction("JZ", i, token, offset=5))
                self.add_instruction(Instruction("JL", i, token, offset=4))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("FALSE", i, token))
                self.add_instruction(Instruction("JMPR", i, token, offset=3))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("TRUE ", i, token))

            elif token in ['SWAP', 'DUP', 'DROP', 'OVER', 'ROT']:
                self.add_instruction(Instruction(token, i, token))

            elif token == '!':
                self.add_instruction(Instruction("SET", i, token))
            elif token == '@':
                self.add_instruction(Instruction("GET", i, token))

            elif token == '.':
                self.add_instruction(Instruction("PRINT", i, token))
            elif token == 'ACCEPT':
                self.add_instruction(Instruction("READ", i, token))

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
                self.add_instruction(Instruction("CALL", i, token, offset=func.call_offset))

            elif token == 'IF':
                self.add_instruction(Instruction("FALSE", i, token))
                self.add_instruction(Instruction("CMP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("DROP", i, token))
                self.add_instruction(Instruction("JZ", i, token, offset=1))
                self.add_instruction(Instruction("JMPR", i, token, offset=1))
                self.add_instruction(Instruction("JMPA", i, token, offset=-1))

                self.recursion_level_if += 1
            elif token == 'THEN':
                self.labels.append((self.recursion_level_if, self.instruction_counter - 1))
                self.recursion_level_if -= 1

            else:
                raise ValueError(f'Unknown token {token}')

        self.add_instruction(Instruction("HLT", -1))

        self.define_functions()

        print(f"Translated {len(self.instructions)} instructions (without address tables):")
        print(self.instructions)

        self.process_if_statements_for_regular()

        self.merge_address_tables()

        # print("LOAD address table values:")
        # self.load.print()
        # print("CALL address table values:")
        # self.call.print()
        # print("JMP address table values:")
        # self.jmp.print()

        return self.instructions, self.data


def main(source_path, output_path):
    with open(source_path, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()

        print("SOURCE CODE:")
        print(source_code)

        print("\n===== translation start =====")
        translator = Translator(source_code)
        instructions, data = translator.translate()
        print("===== translation end =====\n")

        program = {"instructions": instructions, "data": data}
        print("\nTranslated code:")
        print(program)

        with open(output_path, "w", encoding="utf-8") as bin_file:
            bin_file.write(json.dumps(program, indent=4))


if __name__ == '__main__':
    main("inputcode.txt", "outputcode.txt")
