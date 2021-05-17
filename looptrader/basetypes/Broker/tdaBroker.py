"""
The concrete implementation of the generic LoopTrader Broker class for communication with TD Ameritrade.

Classes:

    TdaBroker

Functions:

    get_account()
    place_order()
    get_order()
    cancel_order()
    get_option_chain()
    get_market_hours()
"""

import datetime as dtime
import logging
from collections import OrderedDict
from os import getenv
from typing import Any, Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Broker.abstractBroker import Broker
from basetypes.Component.abstractComponent import Component
from td.client import TDClient
from td.option_chain import OptionChain

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True)
class TdaBroker(Broker, Component):
    """The concrete implementation of the generic LoopTrader Broker class for communication with TD Ameritrade."""

    client_id: str = attr.ib(
        default=getenv("TDAMERITRADE_CLIENT_ID"),
        validator=attr.validators.instance_of(str),
    )
    redirect_uri: str = attr.ib(
        default=getenv("REDIRECT_URL"), validator=attr.validators.instance_of(str)
    )
    account_number: str = attr.ib(
        default=getenv("TDAMERITRADE_ACCOUNT_NUMBER"),
        validator=attr.validators.instance_of(str),
    )
    credentials_path: str = attr.ib(
        default=getenv("CREDENTIALS_PATH"), validator=attr.validators.instance_of(str)
    )
    maxretries: int = attr.ib(
        default=3, validator=attr.validators.instance_of(int), init=False
    )

    def get_account(
        self, request: baseRR.GetAccountRequestMessage
    ) -> baseRR.GetAccountResponseMessage:
        """The function for reading account details from TD Ameritrade."""

        # Build Request
        optionalfields = []

        if request.orders:
            optionalfields.append("orders")
        if request.positions:
            optionalfields.append("positions")

        # Stub response message
        response = baseRR.GetAccountResponseMessage()

        # Get Account Details
        for attempt in range(self.maxretries):
            try:
                acctnum = getenv("TDAMERITRADE_ACCOUNT_NUMBER")
                account = self.getsession().get_accounts(acctnum, fields=optionalfields)
            except Exception:
                logger.exception(
                    "Failed to get Account {}. Attempt #{}".format(acctnum, attempt)
                )
                if attempt == self.maxretries - 1:
                    return response

        securitiesaccount = account.get("securitiesAccount", dict)

        if securitiesaccount is None:
            return response

        # If we requested Orders, build them
        if request.orders:
            response.orders = self.build_account_orders(securitiesaccount)

        # If we requested positions, build them
        if request.positions:
            response.positions = self.build_account_positions(securitiesaccount)

        # Grab Balances
        response.currentbalances = self.build_balances(securitiesaccount)

        # Return Results
        return response

    def build_balances(self, securitiesaccount: dict) -> baseRR.AccountBalance:
        """Builds account balances for getAccount."""
        response = baseRR.AccountBalance()

        currentbalances = securitiesaccount.get("currentBalances", dict)

        response.buyingpower = currentbalances.get(
            "buyingPowerNonMarginableTrade", float
        )
        response.liquidationvalue = currentbalances.get("liquidationValue", float)

        return response

    def build_account_positions(
        self, securitiesaccount: dict
    ) -> list[baseRR.AccountPosition]:
        """Builds a list of Account Positions from a raw list of positions."""
        response = list[baseRR.AccountPosition]()

        positions = securitiesaccount.get("positions")

        if positions is None:
            return response

        for position in positions:
            # Build Position
            accountposition = self.build_account_position(position)
            # Append Position
            response.append(accountposition)

        return response

    @staticmethod
    def build_account_order_leg(leg: dict):
        """Transforms a TDA order leg dictionary into a LoopTrader order leg"""
        accountorderleg = baseRR.AccountOrderLeg()
        accountorderleg.legid = leg.get("legId", int)
        accountorderleg.instruction = leg.get("instruction", str)
        accountorderleg.positioneffect = leg.get("positionEffect", str)
        accountorderleg.quantity = leg.get("quantity", int)

        instrument = leg.get("instrument", dict)

        if instrument is not None:
            accountorderleg.cusip = instrument.get("cusip")
            accountorderleg.symbol = instrument.get("symbol")
            accountorderleg.description = instrument.get("description")
            accountorderleg.putcall = instrument.get("putCall")
        return accountorderleg

    @staticmethod
    def build_account_order(order: dict):
        """Transforms a TDA order dictionary into a LoopTrader order"""

        accountorder = baseRR.AccountOrder()
        accountorder.duration = order.get("duration", str)
        accountorder.quantity = order.get("quantity", int)
        accountorder.filledquantity = order.get("filledQuantity", int)
        accountorder.price = order.get("price", float)
        accountorder.orderid = order.get("orderId", str)
        accountorder.status = order.get("status", str)
        accountorder.enteredtime = order.get("enteredTime", dtime.datetime)
        accountorder.closetime = order.get("closeTime", dtime.datetime)
        accountorder.accountid = order.get("accountId", int)
        accountorder.cancelable = order.get("cancelable", bool)
        accountorder.editable = order.get("editable", bool)
        accountorder.legs = []
        return accountorder

    @staticmethod
    def build_account_position(position: dict):
        """Transforms a TDA position dictionary into a LoopTrader position"""

        accountposition = baseRR.AccountPosition()
        accountposition.shortquantity = position.get("shortQuantity", int)
        accountposition.averageprice = position.get("averagePrice", float)
        accountposition.currentdayprofitloss = position.get(
            "currentDayProfitLoss", float
        )
        accountposition.currentdayprofitlosspercentage = position.get(
            "currentDayProfitLossPercentage", float
        )

        accountposition.marketvalue = position.get("marketValue", float)
        accountposition.longquantity = position.get("longQuantity", int)

        instrument = position.get("instrument", dict)

        if instrument is not None:
            accountposition.assettype = instrument.get("assetType", str)
            accountposition.description = instrument.get("description", str)
            accountposition.putcall = instrument.get("putCall", str)
            accountposition.symbol = instrument.get("symbol", str)
            accountposition.underlyingsymbol = instrument.get("underlyingSymbol", str)
        return accountposition

    def build_account_orders(
        self, securitiesaccount: dict
    ) -> list[baseRR.AccountOrder]:
        """Builds a list of Account Orders from a raw list of orders."""
        response = []

        orders = securitiesaccount.get("orderStrategies", dict)

        order: dict
        for order in orders:
            accountorder = self.build_account_order(order)
            for leg in order.get("orderLegCollection", dict):
                # Build Leg
                accountorderleg = self.build_account_order_leg(leg)
                # Append Leg
                accountorder.legs.append(accountorderleg)
            # Append Order
            response.append(accountorder)

        return response

    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> Union[baseRR.PlaceOrderResponseMessage, None]:
        """The function for placing an order with TD Ameritrade."""

        # Validate the request
        if request is None:
            logger.error("Order is None")
            raise KeyError("Order is None")

        # Build Request. This is the bare minimum, we could extend the available request parameters in the future
        orderrequest = OrderedDict()
        orderrequest["orderStrategyType"] = request.orderstrategytype
        orderrequest["orderType"] = request.ordertype
        orderrequest["session"] = request.ordersession
        orderrequest["duration"] = request.duration
        orderrequest["price"] = str(request.price)
        orderrequest["orderLegCollection"] = [  # type: ignore
            {
                "instruction": request.instruction,
                "quantity": request.quantity,
                "instrument": {
                    "assetType": request.assettype,
                    "symbol": request.symbol,
                },
            }
        ]

        response = baseRR.PlaceOrderResponseMessage()

        # Log the Order
        logger.info("Your order being placed is: {} ".format(orderrequest))

        # Place the Order
        try:
            orderresponse = self.getsession().place_order(
                account=self.account_number, order=orderrequest
            )
            logger.info("Order {} Placed".format(orderresponse["order_id"]))
        except Exception:
            logger.exception("Failed to place order.")
            return None

        response.orderid = orderresponse.get("order_id")

        # Return the Order ID
        return response

    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> baseRR.GetOrderResponseMessage:
        """Reads a single order from TDA and returns it's details"""

        response = baseRR.GetOrderResponseMessage()

        for attempt in range(self.maxretries):
            try:
                order = self.getsession().get_orders(
                    account=self.account_number, order_id=str(request.orderid)
                )
            except Exception:
                logger.exception(
                    "Failed to read order {}.".format(str(request.orderid))
                )
                if attempt == self.maxretries - 1:
                    return response

        response.accountid = order.get("accountId")
        response.closetime = order.get("closeTime")
        response.enteredtime = order.get("enteredTime")
        response.orderid = order.get("orderId")
        response.status = order.get("status")

        orderleg = order.get("orderLegCollection")[0]

        if orderleg is not None:
            response.instruction = orderleg.get("instruction")
            response.positioneffect = orderleg.get("positionEffect")

        instrument = orderleg.get("instrument")

        if instrument is not None:
            response.description = instrument.get("description")
            response.symbol = instrument.get("symbol")

        return response

    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> baseRR.GetOptionChainResponseMessage:
        """Reads the option chain for a given symbol, date range, and contract type."""

        if request is None:
            logger.error("OptionChainRequest is None.")

        optionchainrequest = self.build_option_chain_request(request)

        optionchainobj = OptionChain()
        optionchainobj.query_parameters = optionchainrequest

        response = baseRR.GetOptionChainResponseMessage()

        if not optionchainobj.validate_chain():
            logger.exception("Chain Validation Failed. {}".format(optionchainobj))
            return response

        for attempt in range(self.maxretries):
            try:
                optionschain = self.getsession().get_options_chain(optionchainrequest)
            except Exception:
                logger.exception(
                    "Failed to get Options Chain. Attempt #{}".format(attempt)
                )
                if attempt == self.maxretries - 1:
                    return response

        response.symbol = optionschain.get("symbol", str)
        response.status = optionschain.get("status", str)
        response.underlyinglastprice = optionschain.get("underlyingPrice", float)
        response.volatility = optionschain.get("volatility", float)

        response.putexpdatemap = self.build_option_chain(
            dict(optionschain.get("putExpDateMap"))
        )
        response.callexpdatemap = self.build_option_chain(
            dict(optionschain.get("callExpDateMap"))
        )

        return response

    def build_option_chain_request(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> dict[str, Any]:
        """Builds the Option Chain Request Message"""
        return {
            "symbol": request.symbol,
            "contractType": request.contracttype,
            "includeQuotes": "TRUE" if request.includequotes is True else "FALSE",
            "range": request.optionrange,
            "fromDate": request.fromdate,
            "toDate": request.todate,
        }

    def cancel_order(
        self, request: baseRR.CancelOrderRequestMessage
    ) -> baseRR.CancelOrderResponseMessage:
        """Cancels a given order ID."""

        try:
            accountnumber = getenv("TDAMERITRADE_ACCOUNT_NUMBER")
            orderidstr = str(request.orderid)

            cancelresponse = self.getsession().cancel_order(
                account=accountnumber, order_id=orderidstr
            )
        except Exception:
            logger.exception("Failed to cancel order {}.".format(str(request.orderid)))

        response = baseRR.CancelOrderResponseMessage()
        response.responsecode = cancelresponse.get("status_code")

        return response

    def get_market_hours(
        self, request: baseRR.GetMarketHoursRequestMessage
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        """Gets the opening and closing market hours for a given day."""

        markets = [request.market]

        # Get Market Hours
        for attempt in range(self.maxretries):
            try:
                hours = self.getsession().get_market_hours(
                    markets=markets, date=str(request.datetime)
                )
                break
            except Exception:
                logger.exception(
                    "Failed to get market hours for {} on {}. Attempt #{}".format(
                        markets, request.datetime, attempt
                    ),
                )
                if attempt == self.maxretries - 1:
                    return None

        markettype: dict
        for markettype in hours.values():

            details: dict
            for type, details in markettype.items():
                if type == request.product:
                    sessionhours = details.get("sessionHours", dict)

                    return self.process_session_hours(sessionhours, details)

        return None

    def process_session_hours(
        self, sessionhours: dict, details: dict
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Iterates session hours to build a market hours response"""
        for session, markethours in sessionhours.items():
            if session == "regularMarket":
                response = self.build_market_hours_response(markethours, details)
        return response

    @staticmethod
    def build_market_hours_response(
        markethours: list, details: dict
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Builds a Market Hours reponse Message for given details"""
        response = baseRR.GetMarketHoursResponseMessage()

        startdt = dtime.datetime.strptime(
            str(dict(markethours[0]).get("start")), "%Y-%m-%dT%H:%M:%S%z"
        )
        enddt = dtime.datetime.strptime(
            str(dict(markethours[0]).get("end")), "%Y-%m-%dT%H:%M:%S%z"
        )
        response.start = startdt.astimezone(dtime.timezone.utc)
        response.end = enddt.astimezone(dtime.timezone.utc)
        response.isopen = details.get("isOpen", bool)

        return response

    def getsession(self) -> TDClient:
        """Generates a TD Client session"""

        return TDClient(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            account_number=self.account_number,
            credentials_path=self.credentials_path,
        )

    def getaccesstoken(self):
        """Retrieves a new access token."""

        try:
            self.getsession().grab_access_token()
        except Exception:
            logger.exception("Failed to get access token.")

    # Static Methods
    @staticmethod
    def build_option_chain(
        rawoptionchain: dict,
    ) -> list[baseRR.GetOptionChainResponseMessage.ExpirationDate]:
        """Transforms a TDA option chain dictionary into a LoopTrader option chain"""

        response = []

        expiration: str
        strikes: dict
        for expiration, strikes in rawoptionchain.items():
            exp = expiration.split(":", 1)

            expiry = baseRR.GetOptionChainResponseMessage.ExpirationDate()
            expiry.expirationdate = dtime.datetime.strptime(exp[0], "%Y-%m-%d")
            expiry.daystoexpiration = int(exp[1])
            expiry.strikes = {}

            details: list
            for details in strikes.values():
                detail: dict
                for detail in details:
                    strikeresponse = (
                        baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike()
                    )
                    strikeresponse.strike = detail.get("strikePrice", float)
                    strikeresponse.bid = detail.get("bid", float)
                    strikeresponse.ask = detail.get("ask", float)
                    strikeresponse.delta = detail.get("delta", float)
                    strikeresponse.gamma = detail.get("gamma", float)
                    strikeresponse.theta = detail.get("theta", float)
                    strikeresponse.vega = detail.get("vega", float)
                    strikeresponse.rho = detail.get("rho", float)
                    strikeresponse.symbol = detail.get("symbol", str)
                    strikeresponse.description = detail.get("description", str)
                    strikeresponse.putcall = detail.get("putCall", str)
                    strikeresponse.settlementtype = detail.get("settlementType", str)
                    strikeresponse.expirationtype = detail.get("expirationType", str)

                    expiry.strikes[detail.get("strikePrice", float)] = strikeresponse

            response.append(expiry)

        return response
