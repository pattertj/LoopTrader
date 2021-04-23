import unittest

from BaseTypes.Strategy.cspByDeltaStrategy import CspByDeltaStrategy


class TestCspByDeltaStrategy(unittest.TestCase):
    def setUp(self):
        self.func = CspByDeltaStrategy()

    def test_calculate_order_quantity(self):
        qty = self.func.calculate_order_quantity(4000, 250000)

        self.assertEqual(qty, 3)

    def test_calculate_order_quantity_insufficient(self):
        qty = self.func.calculate_order_quantity(4000, 500)

        self.assertEqual(qty, 0)
