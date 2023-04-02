import contextlib

import pytest
import yaml
import sys
from io import StringIO
from src import translator
import tempfile
import os


@pytest.fixture
def golden_test_input():
    with open('translator_golden.yml', 'r') as file:
        test_data = yaml.safe_load(file)
    return test_data


@pytest.mark.golden_test
@pytest.mark.parametrize("test_case", [
    ("code_hello_world", "output_hello_world"),
    ("code_cat", "output_cat"),
    ("code_prob1", "output_prob1")
])
def test_golden(test_case, golden_test_input):
    code = golden_test_input[test_case[0]]

    with tempfile.TemporaryDirectory() as tmpdir:
        source_file_path = os.path.join(tmpdir, 'source.forth')
        with open(source_file_path, 'w') as source_file:
            source_file.write(code)

        with contextlib.redirect_stdout(StringIO()) as stdout:
            translator.main(source_file_path, os.path.join(tmpdir, 'target.out'))

            actual = stdout.getvalue()
            expected = golden_test_input[test_case[1]]

            assert actual == expected
