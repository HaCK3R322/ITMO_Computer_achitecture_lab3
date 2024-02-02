import json
import os
import unittest
from src.translatorv2 import Translator


class TestTranslator(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.instructions_start_address = 0x00C0
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

    def get_source_and_expected_paths(self, name):
        source_path = os.path.join(self.script_directory, name, 'source.forth')
        expected_path = os.path.join(self.script_directory, name, 'expected.lab')
        return source_path, expected_path

    def test_void(self):
        source_path, expected_path = self.get_source_and_expected_paths('void')

        with open(source_path) as source_file:
            with open(expected_path) as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_nested_ifs(self):
        source_path, expected_path = self.get_source_and_expected_paths('nested_ifs')

        with open(source_path) as source_file:
            with open(expected_path) as expected_file:
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
        source_path, expected_path = self.get_source_and_expected_paths('begin_until_inside_function')

        with open(source_path) as source_file:
            with open(expected_path) as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_begin_until_inside_if_then(self):
        source_path, expected_path = self.get_source_and_expected_paths('begin_until_inside_if_then')

        with open(source_path) as source_file:
            with open(expected_path) as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()
                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

    def test_nested_begin_inside_nested_if_inside_function_inside_begin(self):
        source_path, expected_path = self.get_source_and_expected_paths('nested_begin_inside_nested_if_inside_function_inside_begin')

        with open(source_path) as source_file:
            with open(expected_path) as expected_file:
                source = source_file.read()
                translator = Translator(source)
                translator.translate()

                translated_instructions = translator.convert_instructions_to_list()[self.instructions_start_address:]
                expected_instructions = json.loads(expected_file.read())

                self.assertEqual(translated_instructions, expected_instructions)

