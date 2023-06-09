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
    def __init__(self, code_text, optimize=False):
        self.tokens = code_text.split()

        self.data = []
        self.data.append(-1)  # True pre-buid address
        self.data.append(0)  # False pre-build address
        self.data_TRUE = 0x800
        self.data_FALSE = 0x801
        self.data_start = 0x802

        self.instr = []

        self.vars = []
        self.functions = []

        self.if_stack = []
        self.loop_stack = []
        self.func_stack = []

        self.scope = {"VARIABLE", "BEGIN", "UNTIL", "IF", "THEN",
                      "+", "-", "/", "*", "%", "<", ">", "=",
                      "@", "!",
                      "SWAP", "SET", "DUP", "OVER", "DROP",
                      ".", "ACCEPT"}

        self.optimize = optimize

        self.token_counter = 0

        self.static_digits = []

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

    def is_function(self, token):
        for func in self.functions:
            if token == func['name']:
                return True

        return False

    def get_function_by_name(self, name):
        for func in self.functions:
            if name == func['name']:
                return func

        raise SyntaxError(f"No function found with name \"{name}\"")

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

    def translate_to_instruction(self, opcode, address=None):
        if address is None:
            return {"opcode": opcode, "related_token_index": self.token_counter}
        else:
            return {"opcode": opcode, "address": address, "related_token_index": self.token_counter}

    def translate_IF(self):
        self.if_stack.append(0)

    def translate_THEN(self, number_of_added_instructions):
        to_insert_before = [
            self.translate_to_instruction("PUSH", address=self.data_FALSE),
            self.translate_to_instruction("CMP"),
            self.translate_to_instruction("JZ", address=3 + number_of_added_instructions),
            self.translate_to_instruction("DROP"),
            self.translate_to_instruction("DROP")
        ]

        to_insert_after = [
            self.translate_to_instruction("JMP", address=2),
            self.translate_to_instruction("DROP"),
            self.translate_to_instruction("DROP")
        ]

        instr_before_if = self.instr[:len(self.instr) - number_of_added_instructions]
        instr_in_statement = self.instr[len(self.instr) - number_of_added_instructions:len(self.instr)]

        total = instr_before_if + to_insert_before + instr_in_statement + to_insert_after
        self.instr = total

        self.if_stack.pop()

    def translate_BEGIN(self):
        self.loop_stack.append(0)

    def translate_UNTIL(self, number_of_added_instructions):
        self.instr.append(self.translate_to_instruction("PUSH", address=self.data_FALSE))
        self.instr.append(self.translate_to_instruction("CMP"))
        self.instr.append(self.translate_to_instruction("JNZ", address=3))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("JMP", address=(-number_of_added_instructions - 6)))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))

        self.loop_stack.pop()

    def define_variable(self, name):
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

        self.vars.append({"name": name, "address": self.data_start})
        self.data.append(self.data_start + 1)
        self.data_start += 1
        self.data.append(0)
        self.data_start += 1

    def define_function(self, name):
        if self.is_function(name):
            raise SyntaxError(f"Function with name \"{name}\" already exists!")

        if name.upper() in self.scope:
            raise SyntaxError(f"Invalid function name \"{name}\"")

        if name.lstrip('-+').isdigit():
            raise SyntaxError(f"Function name cannot be numeric")

        # okay i have two ways to define functions:
        # 1 - fast work + allat of code - just inline function
        # 2 - slower work + less code - make jmps
        # keeping in mind that IM STUDENT AND ITS FAKE MODEL with no prediction unit (by now)

        # im gonna just inline functions

        self.functions.append({'name': name, 'instructions': []})
        self.func_stack.append(0)

    def translate_semicolon(self):
        number_of_added_instructions = self.func_stack.pop()
        instr_before_func = self.instr[:len(self.instr) - number_of_added_instructions]
        instr_of_func = self.instr[len(self.instr) - number_of_added_instructions:len(self.instr)]

        self.functions[-1]['instructions'] = instr_of_func
        self.instr = instr_before_func


    def translate_digit(self, token_digit):
        if self.optimize:  # if optimize == True
            digit_found = False
            for digit in self.static_digits:  # try to find already allocated digit with that value and push it
                if digit["value"] == token_digit:
                    digit_found = True
                    self.instr.append(self.translate_to_instruction("PUSH", address=digit["address"]))

            if not digit_found:  # if not found then add to data and remember it
                self.data.append(token_digit)
                self.instr.append(self.translate_to_instruction("PUSH", address=self.data_start))

                self.static_digits.append({"value": token_digit, "address": self.data_start})

                self.data_start += 1
        else:
            self.data.append(token_digit)
            self.instr.append(self.translate_to_instruction("PUSH", address=self.data_start))
            self.data_start += 1

    def translate_comparation(self, symbol):
        self.instr.append(self.translate_to_instruction("CMP"))  # cmp two numbers to set flags

        if symbol == "=":
            self.instr.append(self.translate_to_instruction("JZ", address=4))  # ZF means equal
            address_not_jump = self.data_FALSE
            address_jump = self.data_TRUE
        else:
            self.instr.append(self.translate_to_instruction("JL", address=4))  # there we're watching on NF

            if symbol == ">":
                address_not_jump = self.data_FALSE
                address_jump = self.data_TRUE
            else:
                address_not_jump = self.data_TRUE
                address_jump = self.data_FALSE

        # this will work if jump doesn't happen
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("PUSH", address=address_not_jump))
        self.instr.append(self.translate_to_instruction("JMP", address=3))

        # here we jump
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("PUSH", address=address_jump))

    def translate_ACCEPT(self):
        self.data.append(1)
        one_ptr = self.data_start
        self.data_start += 1

        str_start_ptr = self.data_start
        self.data.append(self.data_start + 1)
        self.data_start += 1

        self.data += [0] * 128
        self.data_start += 128  # allocate 128 cells for string

        self.instr.append(self.translate_to_instruction("PUSH", self.data_FALSE))  # counter

        self.instr.append(self.translate_to_instruction("DUP"))  # dup counter to not lose it
        self.instr.append(self.translate_to_instruction("PUSH", str_start_ptr))  # push str_ptr
        self.instr.append(self.translate_to_instruction("ADD"))  # move ptr to cell correspondly to counter
        self.instr.append(self.translate_to_instruction("READ"))  # read to cell from buffer (doesn't pop stack)

        self.instr.append(self.translate_to_instruction("GET"))  # get value
        self.instr.append(self.translate_to_instruction("PUSH", self.data_FALSE))
        self.instr.append(self.translate_to_instruction("CMP"))
        self.instr.append(self.translate_to_instruction("JZ", address=5))  # if value (char) is 0, end
        self.instr.append(self.translate_to_instruction("DROP"))  # if char is not 0, then drop all shit
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("PUSH", one_ptr))  # and increase counter by 1
        self.instr.append(self.translate_to_instruction("ADD"))
        self.instr.append(self.translate_to_instruction("JMP", address=-13))  # move to the next char
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("DROP"))
        self.instr.append(self.translate_to_instruction("PUSH", address=str_start_ptr))  # push str address

    def translate_direct(self, token):
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

        self.instr.append(self.translate_to_instruction(opcode))

    def translate(self):
        # fast checking on syntax errors
        self.check_contructions()

        # some warnings
        try:
            self.zero_division_check()
        except Warning as warning:
            print("----- WARNING: ", warning, " -----")

        self.token_counter = 0

        while self.token_counter < len(self.tokens):
            instr_len_before = len(self.instr)
            token = self.tokens[self.token_counter]
            print("TRANSLATION (" + str(self.token_counter) + "): token: " + token)

            if token.upper() == "IF":
                self.translate_IF()
            elif token.upper() == "THEN":
                number_of_added_instructions = self.if_stack[len(self.if_stack) - 1]
                self.translate_THEN(number_of_added_instructions)

            elif token.upper() == "BEGIN":
                self.translate_BEGIN()
            elif token.upper() == "UNTIL":
                number_of_added_instructions = self.loop_stack[len(self.loop_stack) - 1]
                self.translate_UNTIL(number_of_added_instructions)

            elif token.upper() == "VARIABLE":
                name = self.tokens[self.token_counter + 1]
                self.define_variable(name)
                self.token_counter += 1

            elif self.is_variable(token):
                var = self.get_variable_by_name(token)
                address = var["address"]

                print(f'USING VAR name={var["name"]} address={address}')

                self.instr.append(self.translate_to_instruction("PUSH", address=address))

            elif token[0] == ':':
                if len(token.split(':')) > 2:
                    raise SyntaxError('Function name cannot contain \":\". Right syntax: <:><fnc_name><space><code...>')

                self.define_function(token.split(':')[1])

            elif token == ';':
                self.translate_semicolon()

            elif self.is_function(token):
                self.instr += self.get_function_by_name(token)['instructions']

            # if token is some digit value
            elif token.lstrip('-+').isdigit():
                token_digit = int(token)
                self.translate_digit(token_digit)

            elif token.upper() in {'=', '<', '>'}:
                symbol = token
                self.translate_comparation(symbol)

            elif token.upper() in {"+", "-", "%", "*", "/", "!", "@", ".", "SWAP", "SET", "DUP", "OVER", "DROP"}:
                self.translate_direct(token)

            elif token.upper() == "ACCEPT":
                self.translate_ACCEPT()

            else:
                raise SyntaxError(f'Unrecognizible token #{self.token_counter - 1}: \"{token}\"')

            number_of_added_instructions = len(self.instr) - instr_len_before

            # WHY SO COMPLICATED XD? make easier
            if len(self.if_stack) > 0:
                for if_addedd_instr_index in range(len(self.if_stack)):
                    self.if_stack[if_addedd_instr_index] += number_of_added_instructions

            if len(self.loop_stack) > 0:
                for loop_addedd_instr_index in range(len(self.loop_stack)):
                    self.loop_stack[loop_addedd_instr_index] += number_of_added_instructions

            if len(self.func_stack) > 0:
                for func_added_instr_index in range(len(self.func_stack)):
                    self.func_stack[func_added_instr_index] += number_of_added_instructions

            self.token_counter += 1

        self.instr.append({"opcode": "HLT"})

        print(f"Len instructions: {len(self.instr)}; Len data: {len(self.data)}")
        return self.instr, self.data


def main(filepath, outpath):
    with open(filepath, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()

        print("SOURCE CODE:")
        print(source_code)

        print("\n===== translation start =====")
        translator = Translator(source_code, optimize=True)
        instructions, data = translator.translate()
        print("===== translation end =====\n")

        program = {"instructions": instructions, "data": data}
        print("\nTranslated code:")
        print(program)

        print()
        print(get_pseudo_code(instructions))
        print()
        print(data)

        with open(outpath, "w", encoding="utf-8") as bin_file:
            bin_file.write(json.dumps(program, indent=4))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
