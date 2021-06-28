# import datetime as dt

# import basetypes.Mediator.reqRespTypes as baseRR
# from basetypes.Broker.tdaBroker import TdaBroker


# def test_get_account():
#     broker = TdaBroker(id="individual")
#     broker.maxretries = 3

#     request = baseRR.GetAccountRequestMessage("", True, True)
#     response = broker.get_account(request)

#     assert response is not None
#     assert response.currentbalances is not None
#     assert response.positions is not None
#     assert response.currentbalances.liquidationvalue is not None
#     assert response.currentbalances.buyingpower is not None


# def test_get_order():
#     broker = TdaBroker()
#     broker.maxretries = 3

#     requestorderid = 4240878201
#     request = baseRR.GetOrderRequestMessage(requestorderid)
#     response = broker.get_order(request)

#     assert response is not None
#     assert response.orderid == requestorderid


# def test_cancel_order():
#     broker = TdaBroker()
#     broker.maxretries = 3

#     requestorderid = 4240878201
#     request = baseRR.CancelOrderRequestMessage(requestorderid)
#     response = broker.cancel_order(request)

#     assert response is not None
#     assert response.responsecode == 200


# RUN AT YOUR OWN RISK, THIS COULD OPEN NEW POSITIONS ON YOUR ACCOUNT. YOU MAY NEED TO REVISE THE SYMBOL
# def test_place_order(self):
#     request = baseRR.PlaceOrderRequestMessage(price=.01, quantity=1, symbol='AAPL_040521P60')
#     response = self.func.place_order(request)

#     self.assertIsNotNone(response)


# def test_get_option_chain():
#     broker = TdaBroker()
#     broker.maxretries = 3

#     request = baseRR.GetOptionChainRequestMessage(
#         symbol="$SPX.X",
#         contracttype="PUT",
#         includequotes=True,
#         optionrange="OTM",
#         fromdate=dt.date.today(),
#         todate=dt.date.today() + dt.timedelta(days=4),
#     )
#     response = broker.get_option_chain(request)

#     for foo, bar in response.putexpdatemap[1].strikes.items():
#         print(foo)
#         print(bar)

#     assert response is not None
#     assert response.status is not None
#     assert response.status == "SUCCESS"
#     assert response.symbol is not None
#     assert response.symbol == "$SPX.X"
#     assert response.underlyinglastprice is not None
#     assert response.underlyinglastprice >= 0
#     assert response.putexpdatemap is not None
#     assert len(response.putexpdatemap) > 0
#     assert response.callexpdatemap is not None
#     assert len(response.callexpdatemap) == 0


# def test_get_market_hours():
#     broker = TdaBroker()
#     broker.maxretries = 3

#     request = baseRR.GetMarketHoursRequestMessage(
#         datetime=dt.datetime.now(), market="OPTION", product="IND"
#     )
#     response = broker.get_market_hours(request)

#     assert response is not None
