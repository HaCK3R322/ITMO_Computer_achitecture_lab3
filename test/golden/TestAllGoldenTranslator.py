import logging
import tempfile
import os
import unittest

from src.translatorv2 import main as translator_main
from src.translatorv2 import configure_logger


class TestAllGoldenTranslator(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.maxDiff = None
        self.script_directory = os.path.dirname(os.path.abspath(__file__))

    def are_files_equal(self, file1_path, file2_path):
        with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
            for line1, line2 in zip(file1, file2):
                if line1 != line2:
                    print(f'Line1 != Line2:\n\"{line1}\"\n!=\n\"{line2}\"')
                    return False

            if len(file1.readlines()) != len(file2.readlines()):
                print('Number of lines in the files is not equal.')
                return False

        return True

    def test_cat(self):
        log_folder = os.path.join(self.script_directory, 'log', 'translator', 'cat_logger')
        cat_logger = configure_logger(logging_level=logging.INFO, logger_name="cat_logger", log_folder=log_folder)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file_path = os.path.join(self.script_directory, 'examples', 'cat.forth')
            target_file_path = os.path.join(tmpdir, 'program.lab')

            translator_main(source_file_path, target_file_path, cat_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'translator_cat.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'translator', 'cat_logger', 'cat_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))

    def test_hello_world(self):
        log_folder = os.path.join(self.script_directory, 'log', 'translator', 'hello_world_logger')
        hello_world_logger = configure_logger(logging_level=logging.INFO, logger_name="hello_world_logger",
                                              log_folder=log_folder)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file_path = os.path.join(self.script_directory, 'examples', 'hello_world.forth')
            target_file_path = os.path.join(tmpdir, 'program.lab')

            translator_main(source_file_path, target_file_path, hello_world_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'translator_hello_world.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'translator', 'hello_world_logger',
                                           'hello_world_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))

    def test_prob1(self):
        log_folder = os.path.join(self.script_directory, 'log', 'translator', 'prob1_logger')
        prob1_logger = configure_logger(logging_level=logging.INFO, logger_name="prob1_logger",
                                        log_folder=log_folder)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file_path = os.path.join(self.script_directory, 'examples', 'prob1.forth')
            target_file_path = os.path.join(tmpdir, 'program.lab')

            translator_main(source_file_path, target_file_path, prob1_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'translator_prob1.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'translator', 'prob1_logger',
                                           'prob1_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))

    def test_hello_user_name(self):
        log_folder = os.path.join(self.script_directory, 'log', 'translator', 'hello_user_name_logger')
        hello_user_name_logger = configure_logger(logging_level=logging.INFO, logger_name="hello_user_name_logger",
                                                  log_folder=log_folder)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file_path = os.path.join(self.script_directory, 'examples', 'hello_user_name.forth')
            target_file_path = os.path.join(tmpdir, 'program.lab')

            translator_main(source_file_path, target_file_path, hello_user_name_logger)

            golden_path = os.path.join(self.script_directory, 'golden', 'translator_hello_user_name.log')
            actual_log_path = os.path.join(self.script_directory, 'log', 'translator', 'hello_user_name_logger',
                                           'hello_user_name_logger.log')

            self.assertTrue(self.are_files_equal(golden_path, actual_log_path))
