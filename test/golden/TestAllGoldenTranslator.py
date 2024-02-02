import logging
import tempfile
import os
import shutil
import unittest

from src.translatorv2 import main as translator_main
from src.translatorv2 import configure_logger


class TestAllGoldenTranslator(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.maxDiff = None

    def are_files_equal(self, file1_path, file2_path):
        with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
            for line1, line2 in zip(file1, file2):
                if line1 != line2:
                    return False
        return True

    def test_cat(self):
        cat_logger = configure_logger(logging_level=logging.INFO, logger_name="cat_logger")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/cat.forth', target_file_path, cat_logger)

            self.assertTrue(self.are_files_equal('golden/translator_cat.log',
                                                 'log/translator/cat_logger/cat_logger.log'))

    def test_hello_world(self):
        hello_world_logger = configure_logger(logging_level=logging.INFO, logger_name="hello_world_logger")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/hello_world.forth', target_file_path, hello_world_logger)

            self.assertTrue(self.are_files_equal('golden/translator_hello_world.log', 'log/translator/hello_world_logger/hello_world_logger.log'))

    def test_prob1(self):
        prob1_logger = configure_logger(logging_level=logging.INFO, logger_name="prob1_logger")

        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/prob1.forth', target_file_path, prob1_logger)

            self.assertTrue(self.are_files_equal('golden/translator_prob1.log', 'log/translator/prob1_logger/prob1_logger.log'))
