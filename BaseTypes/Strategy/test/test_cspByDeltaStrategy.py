import unittest

import BaseTypes.Mediator.reqRespTypes as baseRR
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

    def test_get_best_strike(self):
        strikes = {4000: self.new_strike(4000, .10, 1, 1.1)}

        strikes[3090] = self.new_strike(3090, .09, 1, 1.1)
        strikes[3080] = self.new_strike(3080, .08, 1, 1.1)
        strikes[3070] = self.new_strike(3070, .07, 1, 1.1)
        strikes[3060] = self.new_strike(3060, .06, 1, 1.1)
        strikes[3050] = self.new_strike(3050, .05, .9, 1.0)
        strikes[3040] = self.new_strike(3040, .049, .8, .91)
        strikes[3030] = self.new_strike(3030, .045, .7, .81)
        strikes[3020] = self.new_strike(3020, .041, .6, .71)
        strikes[1010] = self.new_strike(1010, .04, .5, .61)

        strike = self.func.get_best_strike(strikes, .06, 200000)

        self.assertEqual(strike.strike, 1010)

    def new_strike(self, strike: float, delta: float, bid: float, ask: float) -> baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike:
        new = baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike()

        new.strike = strike
        new.delta = delta
        new.bid = bid
        new.ask = ask

        return new

    # def test_process_open_market(self):
    #     now = dt.datetime.now().astimezone(dt.timezone.utc)
    #     nowplus2 = dt.datetime.now().astimezone(dt.timezone.utc) + dt.timedelta(hours=2)

    #     self.func.process_open_market(nowplus2, now)
