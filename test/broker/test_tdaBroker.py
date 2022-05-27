# from basetypes.Broker.tdaBroker import TdaBroker
# import basetypes.Mediator.reqRespTypes as baseRR
# import datetime as dt

# def test_get_account():
#     broker = TdaBroker(id="individual")

#     request = baseRR.GetAccountRequestMessage(2, True, True)
#     response = broker.get_account(request)

#     assert response is not None
#     assert response.currentbalances is not None
#     assert response.positions is not None
#     assert response.currentbalances.liquidationvalue is not None
#     assert response.currentbalances.buyingpower is not None


# def test_get_quote():
#     broker = TdaBroker(id="individual")

#     request = baseRR.GetQuoteRequestMessage(2, ['VGSH'])
#     response = broker.get_quote(request)

#     assert response is not None
#     assert response.instruments is not None
#     assert response.instruments[0].symbol == "VGSH"
#     assert response.instruments[0].askPrice > 0

# def test_get_order():
#     broker = TdaBroker(id="individual")

#     requestorderid = 4240878201
#     request = baseRR.GetOrderRequestMessage(2,requestorderid)
#     response = broker.get_order(request)

#     assert response is not None
#     assert response.order is not None
#     assert response.order.order_id == requestorderid


# def test_cancel_order():
#     broker = TdaBroker(id="individual")

#     requestorderid = 4240878201
#     request = baseRR.CancelOrderRequestMessage(2,requestorderid)
#     response = broker.cancel_order(request)

#     assert response is not None
#     assert response.responsecode == 200


# def test_get_option_chain():
#     broker = TdaBroker(id="individual")

#     request = baseRR.GetOptionChainRequestMessage(
#         strategy_id=2,
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
#     broker = TdaBroker(id="individual")

#     request = baseRR.GetMarketHoursRequestMessage(strategy_id=2,
#         datetime=dt.datetime.now(), market="OPTION", product="IND"
#     )
#     response = broker.get_market_hours(request)

#     assert response is not None
