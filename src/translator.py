import json
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

        self.scope = {"VARIABLE", "BEGIN", "UNTIL", "IF", "THEN",
                      "+", "-", "/", "*", "%", "<", ">", "=",
                      "@", "!",
                      "SWAP", "SET", "DUP", "OVER", "DROP",
                      ".", "ACCEPT"}

    def is_variable(self, token):
        for var in self.vars:
            if token == var["name"]:
                return True

        return False

    def get_variable_by_name(self, name):
        for var in self.vars:
            if name == var["name"]:
                return var

        raise SyntaxError("No variable found with name " + name)

    def check_contructions(self):
        if_count = 0
        then_count = 0
        begin_count = 0
        until_count = 0

        for index, token in enumerate(self.tokens):
            if token.upper() == "IF":
                if_count += 1
            elif token.upper() == "THEN":
                then_count += 1
                if then_count > if_count:
                    raise SyntaxError(f'Syntax error token {index}: closing THEN without opening UNTIL')

            if token.upper() == "BEGIN":
                begin_count += 1
            elif token.upper() == "UNTIL":
                until_count += 1
                if until_count > begin_count:
                    raise SyntaxError(f'Syntax error token {index}: closing UNTIL without opening BEGIN')

        if begin_count != until_count:
            raise SyntaxError(f"Number of \"BEGIN\" and \"UNTIL\" not matched: "
                                   f"begin_count = {begin_count}; "
                                   f"until_count = {until_count}")

        if then_count != if_count:
            raise SyntaxError(f"Number of \"IF\" and \"THEN\" not matched: "
                                   f"if_count = {if_count}; "
                                   f"then_count = {then_count}")

    def zero_division_check(self):
        for index, token in enumerate(self.tokens):
            if token == "/":
                if index > 0:
                    if self.tokens[index - 1] == "0":
                        raise Warning(f"potential zero division related with token #{index}")

    def translate(self, optimize=False):
        # fast checking on syntax errors
        self.check_contructions()

        # some warnings
        try:
            self.zero_division_check()
        except Warning as warning:
            print("----- WARNING: ", warning, " -----")

        static_digits = []

        i = 0

        def translate_to_instruction(opcode, address=None):
            if address is None:
                return {"opcode": opcode, "related_token_index": i}
            else:
                return {"opcode": opcode, "address": address, "related_token_index": i}

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
            elif token.upper() == "VARIABLE":
                if i == len(self.tokens) - 1:
                    raise SyntaxError(f"Not named variable")

                name = self.tokens[i + 1]

                # check if new variable name is unique
                for var in self.vars:
                    if name == var["name"]:
                        raise SyntaxError(f"Variable with name \"{name}\" already exists!")

                # check if name is not some predefined thing
                if name.upper() in self.scope:
                    raise SyntaxError(f"Invalid variable name \"{name}\"")

                # check if variable name is not digit
                if name.lstrip('-+').isdigit():
                    raise SyntaxError(f"Variable name cannot be numeric")

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

                print("nanana im testing gh actionsssss")

                i += 1

            # if token is some digit value
            elif token.lstrip('-+').isdigit():
                if optimize:  # if optimize == True
                    digit_found = False
                    for digit in static_digits:  # try to find already allocated digit with that value and push it
                        if digit["value"] == int(token):
                            digit_found = True
                            self.instr.append(translate_to_instruction("PUSH", address=digit["address"]))

                    if not digit_found:  # if not found then add to data and remember it
                        self.data.append(int(token))
                        self.instr.append(translate_to_instruction("PUSH", address=self.data_start))

                        static_digits.append({"value": int(token), "address": self.data_start})

                        self.data_start += 1
                else:
                    self.data.append(int(token))
                    self.instr.append(translate_to_instruction("PUSH", address=self.data_start))
                    self.data_start += 1

                i += 1

            elif token.upper() == "=":  # a b =   ===>   a == b ? -1 : 0
                self.instr.append(translate_to_instruction("CMP"))

                self.instr.append(translate_to_instruction("JZ", address=4))
                # pushing 0 (false)
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_FALSE))
                self.instr.append(translate_to_instruction("JMP", address=3))
                # pushing -1 (true)
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_TRUE))

                i += 1

            elif token.upper() == "<":  # a b <   ===>   a < b ? -1 : 0
                self.instr.append(translate_to_instruction("CMP"))

                self.instr.append(translate_to_instruction("JL", address=4))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_TRUE))
                self.instr.append(translate_to_instruction("JMP", address=3))

                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_FALSE))

                i += 1

            elif token.upper() == ">":  # a b >   ===>   a > b ? -1 : 0
                self.instr.append(translate_to_instruction("CMP"))

                self.instr.append(translate_to_instruction("JL", address=4))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_FALSE))
                self.instr.append(translate_to_instruction("JMP", address=3))

                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=self.data_TRUE))

                i += 1

            # direct instructions translation
            elif token.upper() in {"+", "-", "%", "*", "/", "!", "@", ".", "SWAP", "SET", "DUP", "OVER", "DROP"}:
                opcode = None
                token = token.upper()
                if token == "+":
                    opcode = "ADD"
                elif token == "-":
                    opcode = "SUB"
                elif token == "%":
                    opcode = "MOD"
                elif token == "*":
                    opcode = "MUL"
                elif token == "/":
                    opcode = "DIV"
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

                self.instr.append(translate_to_instruction("DUP"))  # dup counter to not lose it
                self.instr.append(translate_to_instruction("PUSH", str_start_ptr))  # push str_ptr
                self.instr.append(translate_to_instruction("ADD"))  # move ptr to cell correspondly to counter
                self.instr.append(translate_to_instruction("READ"))  # read to cell from buffer (doesn't pop stack)

                self.instr.append(translate_to_instruction("GET"))  # get value
                self.instr.append(translate_to_instruction("PUSH", self.data_FALSE))
                self.instr.append(translate_to_instruction("CMP"))
                self.instr.append(translate_to_instruction("JZ", address=5))  # if value (char) is 0, end
                self.instr.append(translate_to_instruction("DROP"))  # if char is not 0, then drop all shit
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", one_ptr))  # and increase counter by 1
                self.instr.append(translate_to_instruction("ADD"))
                self.instr.append(translate_to_instruction("JMP", address=-13))  # move to the next char
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("DROP"))
                self.instr.append(translate_to_instruction("PUSH", address=str_start_ptr))  # push str address

                i += 1

            else:
                raise SyntaxError(f'Unrecognizible token #{i - 1}: \"{token}\"')

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
    with open(filepath, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()

        print("SOURCE CODE:")
        print(source_code)

        print("\n===== translation start =====")
        translator = Translator(source_code)
        instructions, data = translator.translate(optimize=True)
        print("===== translation end =====\n")

        program = {"instructions": instructions, "data": data}
        print("\nTranslated code:")
        print(program)

        print()
        print(get_pseudo_code(instructions))
        print()
        print(data)

        with open("../program.bin", "w", encoding="utf-8") as bin_file:
            bin_file.write(json.dumps(program, indent=4))


if __name__ == '__main__':
    main(sys.argv[1])
