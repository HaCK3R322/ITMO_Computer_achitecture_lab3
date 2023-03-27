from opcode import Opcode, write_program
import sys

# выходной файл разделен на две части:
# 1:  .start
# 2:      PUSH 0x800
# 3:      PUSH 0x801
# 4:     ADD
# 5:     HLT
# 6:  .data
# 7:      0x800 тут
# 8:      0x801 хранятся
# 9:      0x802 все
# 10:     0x803 переменные
#
# что представляется в виде JSON как
# {
#     "instructions": [
#         {"opcode": "PUSH", "address": 2048},
#         {"opcode": "PUSH", "address": 2049},
#         {"opcode": "ADD"},
#         {"opcode": "HLT"}
#     ],
#     "data": [
#         тут,
#         хранятся,
#         все,
#         переменные
#     ]
# }


def translate_to_instruction(opcode, address=None):
    if address is None:
        return {"opcode": opcode}
    else:
        return {"opcode": opcode, "address": address}


def get_pseudo_code(instructions):
    result = ""
    for instr in instructions:
        if instr["opcode"] == "PUSH":
            result += f'PUSH {hex(instr["address"])}\n'
        elif instr["opcode"] in {"JMP", "JZ", "JNZ"}:
            result += f'{instr["opcode"]} +{instr["address"]}\n'
        else:
            result += f'{instr["opcode"]}\n'

    return result


class Translator:
    def __init__(self, code_text):
        self.tokens = code_text.split()

        self.data = []
        self.data.append(-1)  # True pre-buid address
        self.data.append(0)  # False pre-build address
        self.data_TRUE = 0x800
        self.data_FALSE = 0x801
        self.data_start = 0x802

        self.vars = []

        self.instr = []

        self.if_stack = []
        self.loop_stack = []

    def is_variable(self, token):
        for var in self.vars:
            if token == var["name"]:
                return True

        return False

    def get_variable_by_name(self, name):
        for var in self.vars:
            if name == var["name"]:
                return var

        raise ValueError("no var with name " + name)

    def translate(self):
        i = 0
        while i < len(self.tokens):
            instr_len_before = len(self.instr)

            token = self.tokens[i]

            print("TRANSLATION (" + str(i) + "): token: " + token)

            if token.upper() == "BEGIN":
                self.loop_stack.append(0)

                i += 1
            elif token.upper() == "UNTIL":
                assert len(self.loop_stack) > 0, f'Syntax error token {i}: closing UNTIL without opening BEGIN'

                number_of_added_instructions = self.loop_stack[len(self.loop_stack) - 1]

                self.instr.append(translate_to_instruction("PUSH", address=self.data_FALSE))
                self.instr.append(translate_to_instruction("CMP"))
                self.instr.append(translate_to_instruction("JNZ", address=3))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("JMP", address=(-number_of_added_instructions - 6)))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))

                self.loop_stack.pop()

                i += 1

            elif token.upper() == "IF":
                self.if_stack.append(0)

                i += 1
            elif token.upper() == "THEN":
                assert len(self.if_stack) > 0, f'Syntax error token {i}: closing THEN without opening IF'

                number_of_added_instructions = self.if_stack[len(self.if_stack) - 1]

                to_insert_before = [
                    translate_to_instruction("PUSH", address=self.data_FALSE),
                    translate_to_instruction("CMP"),
                    translate_to_instruction("JZ", address=3 + number_of_added_instructions),
                    translate_to_instruction("DROP"),
                    translate_to_instruction("DROP")
                ]

                to_insert_after = [
                    translate_to_instruction("JMP", address=2),
                    translate_to_instruction("DROP"),
                    translate_to_instruction("DROP")
                ]

                instr_before_if = self.instr[:len(self.instr) - number_of_added_instructions]
                instr_in_statement = self.instr[len(self.instr) - number_of_added_instructions:len(self.instr)]

                total = instr_before_if + to_insert_before + instr_in_statement + to_insert_after
                self.instr = total

                self.if_stack.pop()

                i += 1

            # variable translation logic
            elif token == "variable":
                self.vars.append({"name": self.tokens[i + 1], "address": self.data_start})
                self.data.append(self.data_start + 1)
                self.data_start += 1
                self.data.append(0)
                self.data_start += 1

                i += 2

            elif self.is_variable(token):
                var = self.get_variable_by_name(token)
                address = var["address"]

                print(f'USING VAR name={var["name"]} address={address}')

                self.instr.append(translate_to_instruction("PUSH", address=address))

                i += 1

            elif token.lstrip('-+').isdigit():
                self.data.append(int(token))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_start))
                self.data_start += 1

                i += 1

            elif token.upper() == "=":
                self.instr.append(translate_to_instruction("CMP"))

                self.instr.append(translate_to_instruction("JZ", address=4))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_FALSE))
                self.instr.append(translate_to_instruction("JMP", address=3))

                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_TRUE))

                i += 1

            # direct instructions translation
            elif token.upper() in {"+", "-", "%", "!", "@", ".", "SWAP", "SET", "DUP", "OVER", "DROP"}:
                opcode = None
                token = token.upper()
                if token == "+":
                    opcode = "ADD"
                elif token == "-":
                    opcode = "SUB"
                elif token == "%":
                    opcode = "MOD"
                elif token == "!":
                    opcode = "SET"
                elif token == "@":
                    opcode = "GET"
                elif token == ".":
                    opcode = "PRINT"

                elif token in {"SWAP", "DUP", "OVER", "DROP"}:
                    opcode = token

                self.instr.append(translate_to_instruction(opcode))

                i += 1

            elif token.upper() == "ACCEPT":
                self.data.append(1)
                one_ptr = self.data_start
                self.data_start += 1

                str_start_ptr = self.data_start
                self.data.append(self.data_start + 1)
                self.data_start += 1

                self.data += [0] * 128
                self.data_start += 128  # allocate 128 cells for string

                self.instr.append(translate_to_instruction("PUSH", self.data_FALSE))  # counter

                self.instr.append(translate_to_instruction("DUP"))
                self.instr.append(translate_to_instruction("PUSH", str_start_ptr))
                self.instr.append(translate_to_instruction("ADD"))
                self.instr.append(translate_to_instruction("READ"))  # read doesn't pop stack

                self.instr.append(translate_to_instruction("GET"))
                self.instr.append(translate_to_instruction("PUSH", self.data_FALSE))
                self.instr.append(translate_to_instruction("CMP"))
                self.instr.append(translate_to_instruction("JZ", address=5))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", one_ptr))
                self.instr.append(translate_to_instruction("ADD"))
                self.instr.append(translate_to_instruction("JMP", address=-13))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=str_start_ptr))

                i += 1



            else:
                raise NameError(f'Unrecognizible token #{i - 1}: \"{token}\"')

            number_of_added_instructions = len(self.instr) - instr_len_before

            if len(self.if_stack) > 0:
                for if_addedd_instr_index in range(len(self.if_stack)):
                    self.if_stack[if_addedd_instr_index] += number_of_added_instructions

            if len(self.loop_stack) > 0:
                for loop_addedd_instr_index in range(len(self.loop_stack)):
                    self.loop_stack[loop_addedd_instr_index] += number_of_added_instructions

        self.instr.append({"opcode": "HLT"})
        return self.instr, self.data


def main(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        source_code = file.read()

        print("SOURCE CODE:")
        print(source_code)

        print("\n===== translation start =====")
        translator = Translator(source_code)
        instructions, data = translator.translate()
        print("===== translation end =====\n")

        program = {"instructions": instructions, "data": data}
        print("\nTranslated code:")
        print(program)

        print()
        print(get_pseudo_code(instructions))
        print()
        print(data)

        write_program("program.bin", program)


if __name__ == '__main__':
    main(sys.argv[1])
