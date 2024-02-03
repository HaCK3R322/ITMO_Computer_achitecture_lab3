import logging
import tempfile
import os
import shutil
import unittest

from src.model import main as model_main
from src.translatorv2 import main as translator_main


class TestAll(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

    def test_cat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_input_file_path = os.path.join(self.script_directory, 'examples', 'input.txt')
            shutil.copy(original_input_file_path, tmpdir)

            input_file_path = os.path.join(self.script_directory, tmpdir, 'input.txt')
            target_file_path = os.path.join(self.script_directory, tmpdir, 'program.lab')
            output_file_path = os.path.join(self.script_directory, tmpdir, "output.txt")
            source_file_path = os.path.join(self.script_directory, 'examples', "cat.forth")

            translator_main(source_file_path, target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "foo bar 42"

    def test_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_input_file_path = os.path.join(self.script_directory, 'examples', 'input.txt')
            shutil.copy(original_input_file_path, tmpdir)

            input_file_path = os.path.join(self.script_directory, tmpdir, 'input.txt')
            target_file_path = os.path.join(self.script_directory, tmpdir, 'program.lab')
            output_file_path = os.path.join(self.script_directory, tmpdir, "output.txt")
            source_file_path = os.path.join(self.script_directory, 'examples', "hello_world.forth")

            translator_main(source_file_path, target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "Hello world!"

    def test_prob1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_input_file_path = os.path.join(self.script_directory, 'examples', 'input.txt')
            shutil.copy(original_input_file_path, tmpdir)

            input_file_path = os.path.join(self.script_directory, tmpdir, 'input.txt')
            target_file_path = os.path.join(self.script_directory, tmpdir, 'program.lab')
            output_file_path = os.path.join(self.script_directory, tmpdir, "output.txt")
            source_file_path = os.path.join(self.script_directory, 'examples', "prob1.forth")

            translator_main(source_file_path, target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "233168"

    def test_hello_user_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_input_file_path = os.path.join(self.script_directory, 'examples', 'hello_user_name_input.txt')
            shutil.copy(original_input_file_path, tmpdir)

            input_file_path = os.path.join(self.script_directory, tmpdir, 'hello_user_name_input.txt')
            target_file_path = os.path.join(self.script_directory, tmpdir, 'program.lab')
            output_file_path = os.path.join(self.script_directory, tmpdir, "output.txt")
            source_file_path = os.path.join(self.script_directory, 'examples', "hello_user_name.forth")

            translator_main(source_file_path, target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "\nWhat is your name?\n> Hello, Ivan!\n"