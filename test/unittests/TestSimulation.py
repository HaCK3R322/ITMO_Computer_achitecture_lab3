import unittest
from src import Simpulation


class TestTranslator(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)

    def test_print(self):
        instructions = [
            {'opcode': 'PUSH', 'address': 0x800, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},
            {'opcode': 'PUSH', 'address': 0x801, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},
            {'opcode': 'PUSH', 'address': 0x802, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},
            {'opcode': 'PUSH', 'address': 0x803, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},
            {'opcode': 'PUSH', 'address': 0x804, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},
            {'opcode': 'PUSH', 'address': 0x805, 'related_token_index': -1},
            {'opcode': 'PRINT', 'related_token_index': -1},

            {'opcode': 'HLT', 'related_token_index': -1}
        ]

        data = [
            ord('H'),
            ord('e'),
            ord('l'),
            ord('l'),
            ord('o'),
            ord('!')
        ]

        program = {'instructions': instructions, 'data': data}

        output_buffer = []

        simulation = Simpulation(program, [], output_buffer)
        simulation.simulate()

        ideal_output_buffer = [72, 101, 108, 108, 111, 33]

        self.assertEqual(ideal_output_buffer, output_buffer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
