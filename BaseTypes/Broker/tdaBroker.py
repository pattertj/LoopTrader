import datetime as dt
import logging
from collections import OrderedDict
from os import getenv

import attr
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Broker.abstractBroker import Broker
from BaseTypes.Component.abstractComponent import Component
from td.client import TDClient
from td.option_chain import OptionChain

logger = logging.getLogger('autotrader')


@attr.s(auto_attribs=True)
class TdaBroker(Broker, Component):
    client_id: str = attr.ib(default=getenv('TDAMERITRADE_CLIENT_ID'), validator=attr.validators.instance_of(str))
    redirect_uri: str = attr.ib(default=getenv('REDIRECT_URL'), validator=attr.validators.instance_of(str))
    account_number: str = attr.ib(default=getenv('TDAMERITRADE_ACCOUNT_NUMBER'), validator=attr.validators.instance_of(str))
    credentials_path: str = attr.ib(default=getenv('CREDENTIALS_PATH'), validator=attr.validators.instance_of(str))
    maxretries: int = attr.ib(default=3, validator=attr.validators.instance_of(int), init=False)

    def get_account(self, request: baseRR.GetAccountRequestMessage) -> baseRR.GetAccountResponseMessage:
        """
        The function for reading account details from TD Ameritrade.

        Parameters:
        request (GetAccountRequestMessage): Generic request message for reading account details

        Returns:
        GetAccountResponseMessage: Generic response mesage for account details

        """

        # Build Request
        optionalfields = []

        if request.orders:
            optionalfields.append('orders')
        if request.positions:
            optionalfields.append('positions')

        # Get Account Details
        for attempt in range(self.maxretries):
            try:
                account = self.getsession().get_accounts(
                    getenv('TDAMERITRADE_ACCOUNT_NUMBER'), fields=optionalfields)
            except Exception:
                # Work backwards on severity level of logging based on the maxretry value
                if attempt >= self.maxretries:
                    logger.exception('Failed to get Account {}. Attempt #{}'.format(getenv('TDAMERITRADE_ACCOUNT_NUMBER'), attempt))
                elif attempt == self.maxretries - 1:
                    logger.error('Failed to get Account {}. Attempt #{}'.format(getenv('TDAMERITRADE_ACCOUNT_NUMBER'), attempt))
                elif attempt == self.maxretries - 2:
                    logger.warning('Failed to get Account {}. Attempt #{}'.format(getenv('TDAMERITRADE_ACCOUNT_NUMBER'), attempt))
                elif attempt <= self.maxretries - 3:
                    logger.info('Failed to get Account {}. Attempt #{}'.format(getenv('TDAMERITRADE_ACCOUNT_NUMBER'), attempt))

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
                    accountorder = self.build_account_order(order)

                    for leg in order.get('orderLegCollection'):
                        # Build Leg
                        accountorderleg = self.build_account_order_leg(leg)

                        # Append Leg
                        accountorder.legs.append(accountorderleg)

                    # Append Order
                    response.orders.append(accountorder)

        # If we requested positions, build them
        if request.positions:
            positions = account.get('securitiesAccount').get('positions')

            # Build Positions
            if positions is not None:
                for position in positions:
                    # Build Position
                    accountposition = self.build_account_position(position)

                    # Append Position
                    response.positions.append(accountposition)

        # Grab Balances
        response.currentbalances.buyingpower = account.get('securitiesAccount').get('currentBalances').get('buyingPowerNonMarginableTrade')
        response.currentbalances.liquidationvalue = account.get('securitiesAccount').get('currentBalances').get('liquidationValue')

        # Return Results
        return response

    def place_order(self, request: baseRR.PlaceOrderRequestMessage) -> baseRR.PlaceOrderResponseMessage:
        """
        The function for placing an order with TD Ameritrade.

        Parameters:
        request (PlaceOrderRequestMessage): Generic request message for placing an Order

        Returns:
        PlaceOrderResponseMessage: Generic response mesage for placing an Order

        """        # Validate the request
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
        except Exception:
            logger.exception("Failed to place order.")

        response = baseRR.PlaceOrderResponseMessage()
        response.orderid = orderresponse.get('order_id')

        # Return the Order ID
        return response

    def get_order(self, request: baseRR.GetOrderRequestMessage) -> baseRR.GetOrderResponseMessage:
        '''Reads a single order from TDA and returns it's details'''

        if request.orderid is None:
            logger.error("Order ID is None.")
            raise KeyError("OrderID was not provided")

        try:
            order = self.getsession().get_orders(account=self.account_number, order_id=str(request.orderid))
        except Exception:
            logger.exception("Failed to read order {}.".format(str(request.orderid)))

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
        '''Reads the option chain for a given symbol, date range, and contract type.'''

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
            for attempt in range(self.maxretries):
                try:
                    optionschain = self.getsession().get_options_chain(optionchainrequest)
                except Exception:
                    # Work backwards on severity level of logging based on the maxretry value
                    if attempt >= self.maxretries:
                        logger.exception('Failed to get Options Chain. Attempt #{}'.format(attempt))
                    elif attempt == self.maxretries - 1:
                        logger.error('Failed to get Options Chain. Attempt #{}'.format(attempt))
                    elif attempt == self.maxretries - 2:
                        logger.warning('Failed to get Options Chain. Attempt #{}'.format(attempt))
                    elif attempt <= self.maxretries - 3:
                        logger.info('Failed to get Options Chain. Attempt #{}'.format(attempt))

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

        response.putexpdatemap = self.build_option_chain(puts)
        response.callexpdatemap = self.build_option_chain(calls)

        return response

    def cancel_order(self, request: baseRR.CancelOrderRequestMessage) -> baseRR.CancelOrderResponseMessage:
        '''Cancels a given order.'''

        if request.orderid is None:
            logger.error("Order ID is None.")
            raise KeyError("OrderID was not provided")

        try:
            cancelresponse = self.getsession().cancel_order(account=getenv('TDAMERITRADE_ACCOUNT_NUMBER'), order_id=str(request.orderid))
        except Exception:
            logger.exception("Failed to cancel order {}.".format(str(request.orderid)))

        response = baseRR.CancelOrderResponseMessage()
        response.responsecode = cancelresponse.get('status_code')

        return response

    def get_market_hours(self, request: baseRR.GetMarketHoursRequestMessage) -> baseRR.GetMarketHoursResponseMessage:
        '''Gets the opening and closing market hours for a given day.'''
        markets = [request.market]

        # Validation
        for market in markets:
            if market in ('FUTURE', 'FOREX', 'BOND'):
                return KeyError("{} markets are not supported at this time.".format(market))

        # Get Market Hours
        for attempt in range(self.maxretries):
            try:
                hours = self.getsession().get_market_hours(markets=markets, date=str(request.datetime))
                break
            except Exception:
                # Work backwards on severity level of logging based on the maxretry value
                if attempt >= self.maxretries:
                    logger.exception('Failed to get market hours for {} on {}. Attempt #{}'.format(markets, request.datetime, attempt),)
                elif attempt == self.maxretries - 1:
                    logger.error('Failed to get market hours for {} on {}. Attempt #{}'.format(markets, request.datetime, attempt))
                elif attempt == self.maxretries - 2:
                    logger.warning('Failed to get market hours for {} on {}. Attempt #{}'.format(markets, request.datetime, attempt))
                elif attempt <= self.maxretries - 3:
                    logger.info('Failed to get market hours for {} on {}. Attempt #{}'.format(markets, request.datetime, attempt))

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
        '''Generates a TD Client session'''

        return TDClient(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            account_number=self.account_number,
            credentials_path=self.credentials_path
        )

    def getaccesstoken(self):
        '''Retrieves a new access token.'''

        try:
            self.getsession().grab_access_token()
        except Exception:
            logger.exception('Failed to get access token.')

    # Helper Function
    @staticmethod
    def build_option_chain(rawoptionchain: dict) -> list[baseRR.GetOptionChainResponseMessage.ExpirationDate]:
        '''Transforms a TDA option chain dictionary into a LoopTrader option chain'''

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

    @staticmethod
    def build_account_position(position: dict):
        '''Transforms a TDA position dictionary into a LoopTrader position'''

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
        return accountposition

    @staticmethod
    def build_account_order_leg(leg: dict):
        '''Transforms a TDA order leg dictionary into a LoopTrader order leg'''
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
        return accountorderleg

    @staticmethod
    def build_account_order(order: dict):
        '''Transforms a TDA order dictionary into a LoopTrader order'''

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
        return accountorder
