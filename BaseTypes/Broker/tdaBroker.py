import datetime as dt
import logging
import re
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
        response.positions = [baseRR.AccountPosition]
        response.orders = [baseRR.AccountOrder]
        response.currentbalances = baseRR.AccountBalance()

        orders = account.get('securitiesAccount').get('orderStrategies')
        positions = account.get('securitiesAccount').get('positions')

        if orders is not None:
            for position in orders:
                accountposition = baseRR.AccountOrder()
                response.orders.append(accountposition)

        if positions is not None:
            for position in account.get('securitiesAccount').get('positions'):
                accountposition = baseRR.AccountPosition()
                accountposition.shortquantity = int(position.get('shortQuantity'))
                accountposition.assettype = position.get('instrument').get('assetType')
                accountposition.averageprice = float(position.get('averagePrice'))
                accountposition.longquantity = int(position.get('longQuantity'))
                accountposition.description = position.get('instrument').get('description')
                accountposition.putcall = position.get('instrument').get('putCall')
                accountposition.symbol = position.get('instrument').get('symbol')
                accountposition.underlyingsymbol = position.get('instrument').get('underlyingSymbol')
                if accountposition.description is not None:
                    match = re.search(r'(\d{1,2}) (\w{3}) (\d{2})', accountposition.description)
                    if match is not None:
                        expiration = dt.datetime.strptime(match.group(), '%d %b %y')
                        accountposition.expirationdate = expiration
                response.positions.append(accountposition)

        response.currentbalances.buyingpower = account.get('securitiesAccount').get('currentBalances').get('buyingPower')
        response.currentbalances.liquidationvalue = account.get('securitiesAccount').get('currentBalances').get('liquidationValue')

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
            logger.info("Order {} Placed".format(orderresponse.get('order_id')))
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

        response.accountid = order.get('accountId')
        response.closetime = order.get('closeTime')
        response.description = order.get('orderLegCollection')[0].get('instrument').get('description')
        response.enteredtime = order.get('enteredTime')
        response.instruction = order.get('orderLegCollection')[0].get('instruction')
        response.orderid = order.get('orderId')
        response.positioneffect = order.get('orderLegCollection')[0].get('positionEffect')
        response.status = order.get('status')
        response.symbol = order.get('orderLegCollection')[0].get('instrument').get('symbol')

        return response

    def convert_expdatemap_to_optionstrike_list(self, expdatemap: dict) -> dict[dt.datetime, list[baseRR.OptionStrike]]:
        response = {}

        for date, options in expdatemap.items():
            optionstrikes = []
            datestring = str(date).split(":", 1)[0]
            datetime = dt.datetime.strptime(datestring, '%Y-%m-%d')

            for strike, details in dict(options).items():
                option = baseRR.OptionStrike()
                option.ask = dict(details[0]).get('ask', float)
                option.bid = dict(details[0]).get('bid', float)
                option.delta = dict(details[0]).get('delta', float)
                option.description = dict(details[0]).get('description', str)
                expiration = dict(details[0]).get('expirationDate', int)
                option.expirationdate = dt.datetime.fromtimestamp(expiration / 1000)
                option.iv = dict(details[0]).get('volatility', float)
                option.putcall = dict(details[0]).get('putCall', str)
                option.strike = float(strike)
                option.symbol = dict(details[0]).get('symbol', str)
                option.theta = dict(details[0]).get('theta', float)
                optionstrikes.append(option)

            response[datetime] = optionstrikes

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
        response.putexpdatemap = self.convert_expdatemap_to_optionstrike_list(optionschain.get('putExpDateMap', dict))
        response.callexpdatemap = self.convert_expdatemap_to_optionstrike_list(optionschain.get('callExpDateMap', dict))

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
        try:
            hours = self.getsession().get_market_hours(markets=request.markets, date=str(request.datetime))
        except Exception as e:
            logger.error('Failed to get market hours.', exc_info=e.message)
            return None

        response = baseRR.GetMarketHoursResponseMessage()

        response.isopen = hours.get('option').get('IND').get('isOpen')

        start = dt.datetime.strptime(hours.get('option').get('IND').get('sessionHours').get('regularMarket')[0].get('start'), '%Y-%m-%dT%H:%M:%S%z').astimezone(dt.timezone.utc)
        response.start = start

        end = dt.datetime.strptime(hours.get('option').get('IND').get('sessionHours').get('regularMarket')[0].get('end'), '%Y-%m-%dT%H:%M:%S%z').astimezone(dt.timezone.utc)
        response.end = end

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
