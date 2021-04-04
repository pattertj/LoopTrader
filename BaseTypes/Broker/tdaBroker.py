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
        optionalfields = []

        if request.orders:
            optionalfields.append('orders')
        if request.positions:
            optionalfields.append('positions')

        try:
            account = self.getsession().get_accounts(
                getenv('TDAMERITRADE_ACCOUNT_NUMBER'), fields=optionalfields)
        except Exception:
            logger.error("Failed to get Account Details.")
            raise KeyError("Failed to get Account Details.")

        response = baseRR.GetAccountResponseMessage()

        try:
            response.orders = account['securitiesAccount']['orderStrategies']
        except KeyError as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.positions = account['securitiesAccount']['positions']
        except KeyError as e:
            self.positions = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.currentbalances = account['securitiesAccount']['currentBalances']
        except KeyError as e:
            response.currentbalances = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

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

        # Return the Order ID
        return orderresponse

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
        response.symbol = optionschain['symbol']
        response.status = optionschain['status']
        response.underlyinglastprice = optionschain['underlyingPrice']
        response.putexpdatemap = optionschain['putExpDateMap']
        response.callexpdatemap = optionschain['callExpDateMap']

        return response

    def cancel_order(self, request: baseRR.CancelOrderRequestMessage) -> baseRR.CancelOrderResponseMessage:
        if request.orderid is None:
            logger.error("Order ID is None.")
            raise KeyError("OrderID was not provided")

        return self.getsession().cancel_order(account=getenv('TDAMERITRADE_ACCOUNT_NUMBER'), order_id=str(request.orderid))

    def get_market_hours(self, request: baseRR.GetMarketHoursRequestMessage) -> baseRR.GetMarketHoursResponseMessage:
        try:
            hours = self.getsession().get_market_hours(markets=request.markets, date=str(request.datetime))
        except Exception as e:
            logger.error('Failed to get market hours.', exc_info=e.message)
            return None

        response = baseRR.GetMarketHoursResponseMessage()

        try:
            response.isopen = hours['option']['option']['isOpen']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.start = hours['option']['option']['sessionHours']['regularMarket'][0]['start']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

        try:
            response.end = hours['option']['option']['sessionHours']['regularMarket'][0]['end']
        except Exception as e:
            self.orders = {}
            logger.info("{} doesn't exist for the account".format(e.args[0]))

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
