import logging
import tempfile
import os
import shutil
import unittest

from src.translatorv2 import main as translator_main


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
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/cat.forth', target_file_path, 'test_cat')

            self.assertTrue(self.are_files_equal('tranlator_cat.log', 'log/translator/test_cat/test_cat.log'))

    def test_hello_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/hello_world.forth', target_file_path, 'test_hello_world')

            self.assertTrue(self.are_files_equal('translator_hello_world.log', 'log/translator/test_hello_world/test_hello_world.log'))

    def test_prob1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file_path = os.path.join(tmpdir, 'program.lab')
            translator_main('examples/prob1.forth', target_file_path, 'test_prob1')

            self.assertTrue(self.are_files_equal('translator_prob1.log', 'log/translator/test_prob1/test_prob1.log'))
