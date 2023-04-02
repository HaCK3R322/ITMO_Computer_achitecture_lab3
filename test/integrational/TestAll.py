import unittest
import contextlib
import pytest
import sys
import yaml
import tempfile
import os
import shutil
from io import StringIO
from src import machine
from src import translator


class TestAll(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)

    def test_cat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'target.out')
            output_file_path = os.path.join(tmpdir, 'out.txt')

            translator.main('examples/cat.forth',
                            target_file_path)
            machine.main(target_file_path, input_file_path, output_file_path)

            with open(output_file_path) as file:
                assert file.read() == "foo bar 000123000"

    def test_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'target.out')
            output_file_path = os.path.join(tmpdir, 'out.txt')

            translator.main('examples/hello_world.forth',
                            target_file_path)
            machine.main(target_file_path, input_file_path, output_file_path)

            with open(output_file_path) as file:
                assert file.read() == "Hello world!"

    def test_prob1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy('examples/input.txt', tmpdir)

            input_file_path = os.path.join(tmpdir, 'input.txt')
            target_file_path = os.path.join(tmpdir, 'target.out')
            output_file_path = os.path.join(tmpdir, 'out.txt')

            translator.main('examples/prob1.forth',
                            target_file_path)
            machine.main(target_file_path, input_file_path, output_file_path)

            with open(output_file_path) as file:
                assert file.read() == "233168"


