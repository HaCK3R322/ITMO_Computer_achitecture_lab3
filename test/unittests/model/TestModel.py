import json
import logging
import unittest
import unittest
import tempfile
import os
import shutil
from src.model import Simulation
from src.model import configure_logger


class TestModel(unittest.TestCase):
    def setUp(self):
        print(self._testMethodDoc)
        self.logger = configure_logger(logging_level=logging.INFO, logger_name="test_model_logger") 

    def test_stack_operations(self):
        simulation = Simulation(self.logger)
        simulation.cu.need_print_state = False

        simulation.cu.stack.push(1)
        simulation.cu.stack.push(2)
        simulation.cu.stack.push(3)

        simulation.cu.dup()
        simulation.cu.rot()
        simulation.cu.swap()
        simulation.cu.drop()
        simulation.cu.over()

        self.assertEqual(simulation.cu.stack.tos, 3)
        self.assertEqual(simulation.cu.stack.get_next(), 2)
        simulation.cu.stack.sp_dec()
        self.assertEqual(simulation.cu.stack.get_next(), 3)
        simulation.cu.stack.sp_dec()
        self.assertEqual(simulation.cu.stack.get_next(), 1)

    def test_arithmetic_operations(self):
        simulation = Simulation(self.logger)
        simulation.cu.need_print_state = False

        simulation.cu.stack.push(27)
        simulation.cu.stack.push(120)
        simulation.cu.stack.push(2)
        simulation.cu.stack.push(9)
        simulation.cu.stack.push(3)
        simulation.cu.stack.push(1)

        simulation.cu.sum()
        simulation.cu.sub()
        simulation.cu.mul()
        simulation.cu.divide()
        simulation.cu.mod()

        self.assertEqual(simulation.cu.stack.tos, 3)

    def test_rstack_operations(self):
        simulation = Simulation(self.logger)
        simulation.cu.need_print_state = False

        simulation.cu.stack.push(1)
        simulation.cu.stack.push(2)
        simulation.cu.stack.push(3)

        simulation.cu.tor()
        simulation.cu.tor()

        self.assertEqual(simulation.cu.stack.tos, 1)
        self.assertEqual(simulation.cu.rstack.tos, 2)
        self.assertEqual(simulation.cu.rstack.get_next(), 3)

        simulation.cu.rfrom()

        self.assertEqual(simulation.cu.stack.tos, 2)
        self.assertEqual(simulation.cu.stack.get_next(), 1)
        self.assertEqual(simulation.cu.rstack.tos, 3)

    def test_cmp(self):
        simulation = Simulation(self.logger)
        simulation.cu.need_print_state = False

        simulation.cu.stack.push(2)
        simulation.cu.stack.push(10)
        simulation.cu.cmp()
        self.assertEqual(simulation.cu.zf, False)
        self.assertEqual(simulation.cu.nf, True)

        simulation.cu.stack.push(10)
        simulation.cu.stack.push(2)
        simulation.cu.cmp()
        self.assertEqual(simulation.cu.zf, False)
        self.assertEqual(simulation.cu.nf, False)

        simulation.cu.stack.push(10)
        simulation.cu.stack.push(10)
        simulation.cu.cmp()
        self.assertEqual(simulation.cu.zf, True)
        self.assertEqual(simulation.cu.nf, False)

    def test_sum_overflow(self):
        simulation = Simulation(self.logger)
        simulation.cu.need_print_state = False

        simulation.cu.stack.push(0xFF)
        simulation.cu.stack.push(10)
        simulation.cu.sum()

        self.assertEqual(simulation.cu.stack.tos, 0x09)
        self.assertEqual(simulation.cu.zf, False)
        self.assertEqual(simulation.cu.nf, False)
        self.assertEqual(simulation.cu.of, True)
