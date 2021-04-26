import datetime as dt
import logging
from collections import OrderedDict
from dataclasses import dataclass
from os import getenv

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Broker.abstractBroker import Broker
from BaseTypes.Component.abstractComponent import Component
from td.client import TDClient
from td.option_chain import OptionChain

logger = logging.getLogger('autotrader')


@dataclass
class TdaBroker(Broker, Component):
    client_id: str = getenv('TDAMERITRADE_CLIENT_ID')
    redirect_uri: str = getenv('REDIRECT_URL')
    account_number: str = getenv('TDAMERITRADE_ACCOUNT_NUMBER')
    credentials_path: str = getenv('CREDENTIALS_PATH')

    def get_account(self, request: baseRR.GetAccountRequestMessage) -> baseRR.GetAccountResponseMessage:

        # Build Request
        optionalfields = []

        if request.orders:
            optionalfields.append('orders')
        if request.positions:
            optionalfields.append('positions')

        # Get Account Details
        try:
            account = self.getsession().get_accounts(
                getenv('TDAMERITRADE_ACCOUNT_NUMBER'), fields=optionalfields)
        except Exception as e:
            logger.error(e)
            raise KeyError("Failed to get Account Details.")

        # Stub response message
        response = baseRR.GetAccountResponseMessage()
        response.positions = []
        response.orders = []
        response.currentbalances = baseRR.AccountBalance()

        # If we requested Orders, build them
        if request.orders:
            orders = account.get('securitiesAccount').get('orderStrategies')

            # Build Orders
            if orders is not None:
                order: dict
                for order in orders:
                    # TODO: Build Order
                    accountorder = baseRR.AccountOrder()
                    accountorder.duration = order.get('duration')
                    accountorder.quantity = order.get('quantity')
                    accountorder.filledquantity = order.get('filledQuantity')
                    accountorder.price = order.get('price')
                    accountorder.orderid = order.get('orderId')
                    accountorder.status = order.get('status')
                    accountorder.enteredtime = order.get('enteredTime')
                    accountorder.closetime = order.get('closeTime')
                    accountorder.accountid = order.get('accountId')
                    accountorder.cancelable = order.get('cancelable')
                    accountorder.editable = order.get('editable')
                    accountorder.legs = []

                    leg: dict
                    for leg in order.get('orderLegCollection'):
                        # TODO: Build Leg
                        accountorderleg = baseRR.AccountOrderLeg()
                        accountorderleg.legid = leg.get('legId')
                        accountorderleg.instruction = leg.get('instruction')
                        accountorderleg.positioneffect = leg.get('positionEffect')
                        accountorderleg.quantity = leg.get('quantity')

                        instrument = dict(leg.get('instrument'))

                        if instrument is not None:
                            accountorderleg.cusip = instrument.get('cusip')
                            accountorderleg.symbol = instrument.get('symbol')
                            accountorderleg.description = instrument.get('description')
                            accountorderleg.putcall = instrument.get('putCall')

                        # Append Leg
                        accountorder.legs.append(accountorderleg)

                    # Append Order
                    response.orders.append(accountorder)

        # If we requested positions, build them
        if request.positions:
            positions = account.get('securitiesAccount').get('positions')

            # Build Positions
            if positions is not None:
                position: dict
                for position in positions:
                    # Build Position
                    accountposition = baseRR.AccountPosition()
                    accountposition.shortquantity = int(position.get('shortQuantity'))
                    accountposition.averageprice = float(position.get('averagePrice'))
                    accountposition.longquantity = int(position.get('longQuantity'))

                    instrument = dict(position.get('instrument'))

                    if instrument is not None:
                        accountposition.assettype = instrument.get('assetType')
                        accountposition.description = instrument.get('description')
                        accountposition.putcall = instrument.get('putCall')
                        accountposition.symbol = instrument.get('symbol')
                        accountposition.underlyingsymbol = instrument.get('underlyingSymbol')

                    # Append Position
                    response.positions.append(accountposition)

        # Grab Balances
        response.currentbalances.buyingpower = account.get('securitiesAccount').get('currentBalances').get('buyingPowerNonMarginableTrade')
        response.currentbalances.liquidationvalue = account.get('securitiesAccount').get('currentBalances').get('liquidationValue')

        # Return Results
        return response

    def place_order(self, request: baseRR.PlaceOrderRequestMessage) -> baseRR.PlaceOrderResponseMessage:
        # Validate the request
        if request is None:
            logger.error("Order is None")
            raise KeyError("Order is None")

        # Build Request. This is the bare minimum, we could extend the available request parameters in the future
        orderrequest = OrderedDict()
        orderrequest['orderStrategyType'] = request.orderstrategytype
        orderrequest['orderType'] = request.ordertype
        orderrequest['session'] = request.ordersession
        orderrequest['duration'] = request.duration
        orderrequest['price'] = request.price
        orderrequest['orderLegCollection'] = [
            {
                'instruction': request.instruction,
                'quantity': request.quantity,
                'instrument': {
                    'assetType': request.assettype,
                    'symbol': request.symbol
                }
            }
        ]

        # Log the Order
        logger.info("Your order being placed is: {} ".format(orderrequest))

        # Place the Order
        try:
            orderresponse = self.getsession().place_order(
                account=self.account_number, order=orderrequest)
            logger.info("Order {} Placed".format(orderresponse['order_id']))
        except Exception as e:
            logger.error('Error at %s', 'Place Order', exc_info=e.message)
            raise e

        response = baseRR.PlaceOrderResponseMessage()
        response.orderid = orderresponse.get('order_id')

        # Return the Order ID
        return response

    def get_order(self, request: baseRR.GetOrderRequestMessage) -> baseRR.GetOrderResponseMessage:
        if request.orderid is None:
            logger.error("Order ID is None.")
            raise KeyError("OrderID was not provided")

        order = self.getsession().get_orders(account=self.account_number, order_id=str(request.orderid))

        response = baseRR.GetOrderResponseMessage()

        try:
            response.accountid = order['accountId']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.closetime = order['closeTime']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.description = order['orderLegCollection'][0]['instrument']['description']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.enteredtime = order['enteredTime']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.instruction = order['orderLegCollection'][0]['instruction']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.orderid = order['orderId']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.positioneffect = order['orderLegCollection'][0]['positionEffect']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.status = order['status']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.symbol = order['orderLegCollection'][0]['instrument']['symbol']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        return response

    def get_option_chain(self, request: baseRR.GetOptionChainRequestMessage) -> baseRR.GetOptionChainResponseMessage:
        if request is None:
            logger.error("OptionChainRequest is None.")

        optionchainrequest = {
            'symbol': request.symbol,
            'contractType': request.contracttype,
            'includeQuotes': "TRUE" if request.includequotes is True else "FALSE",
            'range': request.optionrange,
            'fromDate': request.fromdate,
            'toDate': request.todate
        }

        optionchainobj = OptionChain()
        optionchainobj.query_parameters = optionchainrequest

        if optionchainobj.validate_chain():
            optionschain = self.getsession().get_options_chain(optionchainrequest)
        else:
            logger.error("Invalid OptionChainRequest.")
            raise KeyError("Invalid OptionChainRequest.")

        response = baseRR.GetOptionChainResponseMessage()
        response.symbol = optionschain.get('symbol')
        response.status = optionschain.get('status')
        response.underlyinglastprice = optionschain.get('underlyingPrice')
        response.volatility = optionschain.get('volatility')
        response.putexpdatemap = []
        response.callexpdatemap = []

        puts = dict(optionschain.get('putExpDateMap'))
        calls = dict(optionschain.get('callExpDateMap'))

        response.putexpdatemap = self.get_formatted_option_chain(puts)
        response.callexpdatemap = self.get_formatted_option_chain(calls)

        return response

    def get_formatted_option_chain(self, rawoptionchain: dict) -> list[baseRR.GetOptionChainResponseMessage.ExpirationDate]:
        response = []

        expiration: str
        strikes: dict
        for expiration, strikes in rawoptionchain.items():
            exp = expiration.split(":", 1)

            expiry = baseRR.GetOptionChainResponseMessage.ExpirationDate()
            expiry.expirationdate = exp[0]
            expiry.daystoexpiration = int(exp[1])
            expiry.strikes = {}

            details: list
            for details in strikes.values():
                detail: dict
                for detail in details:
                    strikeresponse = baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike()
                    strikeresponse.strike = detail.get('strikePrice')
                    strikeresponse.bid = detail.get('bid')
                    strikeresponse.ask = detail.get('ask')
                    strikeresponse.delta = detail.get('delta')
                    strikeresponse.gamma = detail.get('gamma')
                    strikeresponse.theta = detail.get('theta')
                    strikeresponse.vega = detail.get('vega')
                    strikeresponse.rho = detail.get('rho')
                    strikeresponse.symbol = detail.get('symbol')
                    strikeresponse.description = detail.get('description')
                    strikeresponse.putcall = detail.get('putCall')
                    strikeresponse.settlementtype = detail.get('settlementType')
                    strikeresponse.expirationtype = detail.get('expirationType')

                    expiry.strikes[float(detail.get('strikePrice'))] = strikeresponse

            response.append(expiry)

        return response

    def cancel_order(self, request: baseRR.CancelOrderRequestMessage) -> baseRR.CancelOrderResponseMessage:
        if request.orderid is None:
            logger.error("Order ID is None.")
            raise KeyError("OrderID was not provided")

        cancelresponse = self.getsession().cancel_order(account=getenv('TDAMERITRADE_ACCOUNT_NUMBER'), order_id=str(request.orderid))

        response = baseRR.CancelOrderResponseMessage()
        response.responsecode = cancelresponse.get('status_code')

        return response

    def get_market_hours(self, request: baseRR.GetMarketHoursRequestMessage) -> baseRR.GetMarketHoursResponseMessage:
        markets = []

        markets.append(request.market)

        # Validation
        for market in markets:
            if market == 'FUTURE' or market == 'FOREX' or market == 'BOND':
                return KeyError("{} markets are not supported at this time.".format(market))

        # Get Market Hours
        try:
            hours = self.getsession().get_market_hours(markets=markets, date=str(request.datetime))
        except Exception as e:
            logger.error('Failed to get market hours.', exc_info=e.message)
            return None

        market: str
        markettype: dict
        for market, markettype in hours.items():

            type: str
            details: dict
            for type, details in markettype.items():
                if (type == request.product):
                    sessionhours = dict(details.get('sessionHours'))

                    session: str
                    markethours: list
                    for session, markethours in sessionhours.items():
                        if (session == 'regularMarket'):
                            response = baseRR.GetMarketHoursResponseMessage

                            response.start = dt.datetime.strptime(str(dict(markethours[0]).get('start')), "%Y-%m-%dT%H:%M:%S%z").astimezone(dt.timezone.utc)
                            response.end = dt.datetime.strptime(str(dict(markethours[0]).get('end')), "%Y-%m-%dT%H:%M:%S%z").astimezone(dt.timezone.utc)
                            response.isopen = details.get('isOpen')

                            return response

    def getsession(self) -> TDClient:
        return TDClient(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            account_number=self.account_number,
            credentials_path=self.credentials_path
        )

    def getaccesstoken(self):
        self.getsession().grab_access_token()
