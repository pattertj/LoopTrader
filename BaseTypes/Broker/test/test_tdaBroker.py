import datetime as dt
import unittest

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Broker.tdaBroker import TdaBroker


class TestTdaBroker(unittest.TestCase):
    def setUp(self):
        self.func = TdaBroker()

    def test_get_account(self):
        request = baseRR.GetAccountRequestMessage(True, True)
        response = self.func.get_account(request)

        self.assertIsNotNone(response)
        self.assertIsNotNone(response.currentbalances)
        self.assertIsNotNone(response.positions)
        self.assertGreaterEqual(len(response.positions), 1)
        self.assertEqual(len(response.currentbalances), 27)

    def test_get_order(self):
        requestorderid = 4240878201
        request = baseRR.GetOrderRequestMessage(requestorderid)
        response = self.func.get_order(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.orderid, requestorderid)

    def test_get_option_chain(self):
        request = baseRR.GetOptionChainRequestMessage(symbol='$SPX.X', contracttype='PUT', includequotes=True, optionrange='OTM', fromdate=dt.date.today().strftime("%Y-%m-%d"), todate=(dt.date.today() + dt.timedelta(days=4)).strftime("%Y-%m-%d"))
        response = self.func.get_option_chain(request)

        self.assertIsNotNone(response)

        self.assertIsNotNone(response.status)
        self.assertEqual(response.status, 'SUCCESS')

        self.assertIsNotNone(response.symbol)
        self.assertEqual(response.symbol, '$SPX.X')

        self.assertIsNotNone(response.underlyinglastprice)
        self.assertGreaterEqual(response.underlyinglastprice, 0)

        self.assertIsNotNone(response.putexpdatemap)
        self.assertGreaterEqual(len(response.putexpdatemap), 1)

        self.assertEqual(len(response.callexpdatemap), 0)

    def test_get_market_hours(self):
        request = baseRR.GetMarketHoursRequestMessage(datetime=dt.datetime.now(), markets={'OPTION'})
        response = self.func.get_market_hours(request)

        self.assertIsNotNone(response)
        self.assertIsNotNone(response.isopen)


if __name__ == '__main__':
    unittest.main()
