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

    def test_cat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'program.lab')
            output_file_path = os.path.join(tmpdir, "output.txt")

            translator_main('examples/cat.forth', target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "foo bar 42"

    def test_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'program.lab')
            output_file_path = os.path.join(tmpdir, "output.txt")

            translator_main('examples/hello_world.forth', target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "Hello world!"

    def test_prob1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'program.lab')
            output_file_path = os.path.join(tmpdir, "output.txt")

            translator_main('examples/prob1.forth', target_file_path)
            model_main(target_file_path, input_file_path, output_file_path, logging.INFO)

            with open(output_file_path) as file:
                assert file.read() == "233168"