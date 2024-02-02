import logging
import tempfile
import os
import shutil
import unittest

from src.model import main as model_main
from src.model import configure_logger


class TestAllGoldenModel(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.maxDiff = None
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

    def are_files_equal(self, file1_path, file2_path):
        with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
            for line1, line2 in zip(file1, file2):
                if line1 != line2:
                    return False
        return True

    def test_cat(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_folder = os.path.join(self.script_directory, 'log', 'model', 'cat_logger')
            cat_logger = configure_logger(logging_level=logging.INFO, logger_name="cat_logger", log_folder=log_folder)
            output_file_path = os.path.join(tmpdir, 'output.txt')
            program_file_path = 'programs/cat.lab'
            input_file_path = 'examples/input.txt'

            model_main(program_file_path, input_file_path, output_file_path, logger=cat_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'model_cat.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'model', 'cat_logger',
                                           'cat_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))

    def test_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_folder = os.path.join(self.script_directory, 'log', 'model', 'hello_world_logger')
            hello_world_logger = configure_logger(logging_level=logging.INFO, logger_name="hello_world_logger", log_folder=log_folder)
            output_file_path = os.path.join(tmpdir, 'output.txt')
            program_file_path = 'programs/hello_world.lab'
            input_file_path = 'examples/input.txt'

            model_main(program_file_path, input_file_path, output_file_path, logger=hello_world_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'model_hello_world.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'model', 'hello_world_logger',
                                           'hello_world_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))

    def test_prob1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_folder = os.path.join(self.script_directory, 'log', 'model', 'prob1_logger')
            prob1_logger = configure_logger(logging_level=logging.INFO, logger_name="prob1_logger", log_folder=log_folder)
            output_file_path = os.path.join(tmpdir, 'output.txt')
            program_file_path = 'programs/prob1.lab'
            input_file_path = 'examples/input.txt'

            model_main(program_file_path, input_file_path, output_file_path, logger=prob1_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'model_prob1.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'model', 'prob1_logger',
                                           'prob1_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))
