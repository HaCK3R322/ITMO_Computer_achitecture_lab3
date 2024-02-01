import json
import unittest
import unittest
import tempfile
import os
import shutil
from src.model import main as model_main
from src.translatorv2 import Translator


class TestTranslator(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.instructions_start_address = 0x00C0

    def test_void(self):
        with open('void/source.forth') as source_file:
            with open('void/expected.lab') as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_nested_ifs(self):
        with open('nested_ifs/source.forth') as source_file:
            with open('nested_ifs/expected.lab') as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_double_variable_declaration(self):
        source = "VARIABLE a VARIABLE a"
        translator = Translator(source)

        with self.assertRaises(SyntaxError):
            translator.translate()

    def test_double_function_declaration(self):
        source = ":func1 123 ; :func1 321 ;"
        translator = Translator(source)

        with self.assertRaises(SyntaxError):
            translator.translate()

    def test_variable_redeclaration_inside_function(self):
        source = "VARIABLE var :func1 VARIABLE var ;"
        translator = Translator(source)
        translator.translate()

        assert len(translator.variables) == 2

    def test_variable_declaration_with_reserved_name(self):
        source = "VARIABLE if"
        translator = Translator(source)
        with self.assertRaises(SyntaxError):
            translator.translate()

    def test_variable_declaration_with_decimal_name(self):
        source = "VARIABLE 2lol"
        translator = Translator(source)
        with self.assertRaises(SyntaxError):
            translator.translate()

    def test_function_declaration_inside_function(self):
        source = ":func1 :func2 ; ;"
        translator = Translator(source)
        with self.assertRaises(SyntaxError):
            translator.translate()

    def test_begin_until_inside_function(self):
        with open('begin_until_inside_function/source.forth') as source_file:
            with open('begin_until_inside_function/expected.lab') as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_begin_until_inside_if_then(self):
        with open('begin_until_inside_if_then/source.forth') as source_file:
            with open('begin_until_inside_if_then/expected.lab') as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_nested_begin_inside_nested_if_inside_function_inside_begin(self):
        with open('nested_begin_inside_nested_if_inside_function_inside_begin/source.forth') as source_file:
            with open('nested_begin_inside_nested_if_inside_function_inside_begin/expected.lab') as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()

                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)




#
#     def test_translate_if_then(self):
#         code = "IF 10 THEN"
#         translator = Translator(code, optimize=True)
#
#         instructions, data = translator.translate()
#
#         expected_instructions = [{'opcode': 'PUSH', 'address': 2049, 'related_token_index': 2},
#                                  {'opcode': 'CMP', 'related_token_index': 2},
#                                  {'opcode': 'JZ', 'address': 4, 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'PUSH', 'address': 2050, 'related_token_index': 1},
#                                  {'opcode': 'JMP', 'address': 2, 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'HLT'}]
#
#         self.assertEqual(instructions, expected_instructions)
#
#     def test_translate_loop(self):
#         code = "BEGIN 228 UNTIL"
#         translator = Translator(code, optimize=True)
#         instructions, data = translator.translate()
#
#         expected_instructions = [{'opcode': 'PUSH', 'address': 2050, 'related_token_index': 1},
#                                  {'opcode': 'PUSH', 'address': 2049, 'related_token_index': 2},
#                                  {'opcode': 'CMP', 'related_token_index': 2},
#                                  {'opcode': 'JNZ', 'address': 3, 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'JMP', 'address': -7, 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'DROP', 'related_token_index': 2},
#                                  {'opcode': 'HLT'}]
#
#         self.assertEqual(instructions, expected_instructions)
#
#     def test_translate_nested_loop(self):
#         code = "BEGIN 10 BEGIN 20 UNTIL UNTIL"
#         translator = Translator(code, optimize=True)
#         instructions, data = translator.translate()
#
#         expected_instructions = [{'opcode': 'PUSH', 'address': 2050, 'related_token_index': 1},
#                                  {'opcode': 'PUSH', 'address': 2051, 'related_token_index': 3},
#                                  {'opcode': 'PUSH', 'address': 2049, 'related_token_index': 4},
#                                  {'opcode': 'CMP', 'related_token_index': 4},
#                                  {'opcode': 'JNZ', 'address': 3, 'related_token_index': 4},
#                                  {'opcode': 'DROP', 'related_token_index': 4},
#                                  {'opcode': 'DROP', 'related_token_index': 4},
#                                  {'opcode': 'JMP', 'address': -7, 'related_token_index': 4},
#                                  {'opcode': 'DROP', 'related_token_index': 4},
#                                  {'opcode': 'DROP', 'related_token_index': 4},
#                                  {'opcode': 'PUSH', 'address': 2049, 'related_token_index': 5},
#                                  {'opcode': 'CMP', 'related_token_index': 5},
#                                  {'opcode': 'JNZ', 'address': 3, 'related_token_index': 5},
#                                  {'opcode': 'DROP', 'related_token_index': 5},
#                                  {'opcode': 'DROP', 'related_token_index': 5},
#                                  {'opcode': 'JMP', 'address': -16, 'related_token_index': 5},
#                                  {'opcode': 'DROP', 'related_token_index': 5},
#                                  {'opcode': 'DROP', 'related_token_index': 5},
#                                  {'opcode': 'HLT'}]
#
#         self.assertEqual(instructions, expected_instructions)
#
#     def test_variable_declaraion_and_usage(self):
#         code = "variable a a"
#         translator = Translator(code, optimize=True)
#         instructions, data = translator.translate()
#
#         expected_instructions = [{'opcode': 'PUSH', 'address': 0x802, 'related_token_index': 2},
#                                  {'opcode': 'HLT'}]
#
#         expected_data = [-1, 0, 0x803, 0]
#
#         self.assertEqual(instructions, expected_instructions)
#         self.assertEqual(data, expected_data)
#
#     def test_variable_digit_name(self):
#         code = "variable 41"
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#     def test_varaible_redeclaration(self):
#         code = "variable a variable a"
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#     def test_variable_using_defined_names(self):
#         code = "variable IF"
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#         code = "variable +"
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#         code = "variable UNTIL"
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#     def test_unexpected_token(self):
#         code = "2 48 + . this_is_unexpected_token BEGIN IF THEN UNTIL"
#
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#     def test_not_closed_loop(self):
#         code = "BEGIN UNTIL BEGIN BEGIN  UNTIL UNTIL 111 BEGIN BEGIN UNTIL"
#
#         translator = Translator(code, optimize=True)
#
#         with self.assertRaises(SyntaxError):
#             translator.translate()
#
#     def test_data_optimize_translation(self):
#         code = '1 1 1 2 2 2 3 3 3'
#
#         translator_optimize_false = Translator(code, optimize=False)
#         translator_optimize_true = Translator(code, optimize=True)
#
#         instructions, data_optimize_false = translator_optimize_false.translate()
#         instructions, data_optimized_true = translator_optimize_true.translate()
#
#         self.assertNotEqual(data_optimized_true, data_optimize_false)
#
#         excpected_data_optimize_false = [-1, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]
#         excpected_data_optimize_true = [-1, 0, 1, 2, 3]
#
#         self.assertEqual(data_optimize_false, excpected_data_optimize_false)
#         self.assertEqual(data_optimized_true, excpected_data_optimize_true)
#
#     def test_define_and_use_function(self):
#         code = ":func1 1 2 ; func1 func1"
#
#         translator = Translator(code, optimize=True)
#         instructions, data = translator.translate()
#
#         expected_instructions = [{'opcode': 'PUSH', 'address': 2050, 'related_token_index': 1},
#                                  {'opcode': 'PUSH', 'address': 2051, 'related_token_index': 2},
#                                  {'opcode': 'PUSH', 'address': 2050, 'related_token_index': 1},
#                                  {'opcode': 'PUSH', 'address': 2051, 'related_token_index': 2},
#                                  {'opcode': 'HLT'}]
#
#         expected_data = [-1, 0, 1, 2]
#
#         self.assertEqual(expected_instructions, instructions)
#         self.assertEqual(expected_data, data)
#
#
# if __name__ == "__main__":
#     unittest.main(verbosity=2)
