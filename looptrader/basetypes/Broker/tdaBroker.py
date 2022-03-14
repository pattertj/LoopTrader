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
import re
from collections import OrderedDict
from typing import Any, Union

import attr
import basetypes.Mediator.baseModels as baseModels
import basetypes.Mediator.reqRespTypes as baseRR
import yaml
from basetypes.Broker.abstractBroker import Broker
from basetypes.Component.abstractComponent import Component
from td.client import TDClient
from td.option_chain import OptionChain

logger = logging.getLogger("autotrader")
DT_REGEX = "%Y-%m-%dT%H:%M:%S%z"


@attr.s(auto_attribs=True)
class TdaBroker(Broker, Component):
    """The concrete implementation of the generic LoopTrader Broker class for communication with TD Ameritrade."""

    id: str = attr.ib(validator=attr.validators.instance_of(str))
    client_id: str = attr.ib(validator=attr.validators.instance_of(str), init=False)
    redirect_uri: str = attr.ib(validator=attr.validators.instance_of(str), init=False)
    account_number: str = attr.ib(
        validator=attr.validators.instance_of(str), init=False
    )
    credentials_path: str = attr.ib(
        validator=attr.validators.instance_of(str), init=False
    )
    maxretries: int = attr.ib(
        default=3, validator=attr.validators.instance_of(int), init=False
    )

    def __attrs_post_init__(self):
        with open("config.yaml", "r") as file:
            # Read Brokerage Config
            brokerage_config: dict
            brokerage_config = yaml.safe_load(file)

            # Parse Config
            broker: str
            accounts: dict
            for broker, accounts in brokerage_config.items():
                if broker == "tdabroker":
                    account: str
                    details: dict
                    for account, details in accounts.items():
                        # If we find a match, read details
                        if account == self.id:
                            self.client_id = details.get("clientid")
                            self.account_number = details.get("account")
                            self.redirect_uri = details.get("url")
                            self.credentials_path = details.get("credentials")
                            return

            # If no match, raise exception
            raise RuntimeError("No credentials found in config.yaml")

    ########
    # Read #
    ########
    def get_account(
        self, request: baseRR.GetAccountRequestMessage
    ) -> Union[baseRR.GetAccountResponseMessage, None]:
        """The function for reading account details from TD Ameritrade."""

        # Build Request
        optionalfields = []

        if request.orders:
            optionalfields.append("orders")
        if request.positions:
            optionalfields.append("positions")

        # Get Account Details
        for attempt in range(self.maxretries):
            try:
                account = self.getsession().get_accounts(
                    self.account_number, fields=optionalfields
                )
            except Exception:
                logger.exception(
                    f"Failed to get Account {self.account_number}. Attempt #{attempt}"
                )

                if attempt == self.maxretries - 1:
                    return None

        if account is None:
            return None

        securitiesaccount = account.get("securitiesAccount", dict)

        if securitiesaccount is None:
            return None

        return self.build_account_reponse(securitiesaccount)

    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> Union[baseRR.GetOrderResponseMessage, None]:
        """Reads a single order from TDA and returns it's details"""

        for attempt in range(self.maxretries):
            try:
                order = self.getsession().get_orders(
                    account=self.account_number, order_id=str(request.orderid)
                )
            except Exception:
                logger.exception(f"Failed to read order {str(request.orderid)}.")
                if attempt == self.maxretries - 1:
                    return None

        if order is None:
            raise ValueError("No Order to Translate")

        response = baseRR.GetOrderResponseMessage()

        response.order = self.translate_account_order(order)

        # Append StrategyID
        response.order.strategy_id = request.strategy_id

        return response

    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> Union[baseRR.GetOptionChainResponseMessage, None]:
        """Reads the option chain for a given symbol, date range, and contract type."""

        if request is None:
            logger.error("OptionChainRequest is None.")
            return None

        optionchainrequest = self.build_option_chain_request(request)

        optionchainobj = OptionChain()
        optionchainobj.query_parameters = optionchainrequest

        if not optionchainobj.validate_chain():
            logger.exception(f"Chain Validation Failed. {optionchainobj}")
            return None

        for attempt in range(self.maxretries):
            try:
                optionschain = self.getsession().get_options_chain(optionchainrequest)

                if optionschain["status"] == "FAILED":
                    raise BaseException("Option Chain Status Response = FAILED")

            except Exception:
                logger.exception(f"Failed to get Options Chain. Attempt #{attempt}")
                if attempt == self.maxretries - 1:
                    return None

        if optionschain is None:
            return None

        response = baseRR.GetOptionChainResponseMessage()

        response.symbol = optionschain.get("symbol", str)
        response.status = optionschain.get("status", str)
        response.underlyinglastprice = optionschain.get("underlyingPrice", float)
        response.volatility = optionschain.get("volatility", float)

        response.putexpdatemap = self.translate_option_chain(
            dict(optionschain.get("putExpDateMap"))
        )
        response.callexpdatemap = self.translate_option_chain(
            dict(optionschain.get("callExpDateMap"))
        )

        return response

    def get_quote(
        self, request: baseRR.GetQuoteRequestMessage
    ) -> Union[None, baseRR.GetQuoteResponseMessage]:

        for attempt in range(self.maxretries):
            try:
                quotes = self.getsession().get_quotes(request.instruments)
                break
            except Exception:
                logger.exception(f"Failed to get quotes. Attempt #{attempt}")
                if attempt == self.maxretries - 1:
                    return None

        if quotes is None:
            return None

        response = baseRR.GetQuoteResponseMessage()
        response.instruments = []

        quote: dict
        for quote in quotes.values():
            instrument = baseRR.Instrument()
            instrument.symbol = quote.get("symbol", str)
            instrument.bidPrice = quote.get("bidPrice", float)
            instrument.bidSize = quote.get("bidSize", float)
            instrument.askPrice = quote.get("askPrice", float)
            instrument.askSize = quote.get("askSize", float)
            instrument.lastPrice = quote.get("lastPrice", float)
            instrument.openPrice = quote.get("openPrice", float)
            instrument.highPrice = quote.get("highPrice", float)
            instrument.lowPrice = quote.get("lowPrice", float)
            instrument.closePrice = quote.get("closePrice", float)
            instrument.volatility = quote.get("volatility", float)
            response.instruments.append(instrument)

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
                    f"Failed to get market hours for {markets} on {request.datetime}. Attempt #{attempt}"
                )

                if attempt == self.maxretries - 1:
                    return None

        if hours is None:
            return None

        markettype: dict
        for markettype in hours.values():

            details: dict
            for type, details in markettype.items():
                if type == request.product:
                    sessionhours = details.get("sessionHours", dict)

                    return self.process_session_hours(sessionhours, details)

        return None

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

    ############
    # Builders #
    ############
    def build_account_reponse(
        self, securitiesaccount: dict
    ) -> baseRR.GetAccountResponseMessage:
        response = baseRR.GetAccountResponseMessage()

        response.accountnumber = securitiesaccount.get("accountId", int)

        # If we requested Orders, build them if request.orders:
        response.orders = self.build_account_orders(securitiesaccount)

        # If we requested positions, build them if request.positions:
        response.positions = self.build_account_positions(securitiesaccount)

        # Build Balances
        response.currentbalances = self.build_balances(securitiesaccount)
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
            accountposition = self.translate_account_position(position)
            # Append Position
            response.append(accountposition)

        return response

    def build_account_orders(self, securitiesaccount: dict) -> list[baseModels.Order]:
        """Builds a list of Account Orders from a raw list of orders."""
        response: list[baseModels.Order] = []

        orders = securitiesaccount.get("orderStrategies")

        if orders is None:
            return response
        order: dict
        for order in orders:
            accountorder = self.translate_account_order(order)

            # Append Order
            response.append(accountorder)

        return response

    @staticmethod
    def build_market_hours_response(
        markethours: list, details: dict
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Builds a Market Hours reponse Message for given details"""
        response = baseRR.GetMarketHoursResponseMessage()

        startdt = dtime.datetime.strptime(
            str(dict(markethours[0]).get("start")), DT_REGEX
        )
        enddt = dtime.datetime.strptime(str(dict(markethours[0]).get("end")), DT_REGEX)
        response.start = startdt.astimezone(dtime.timezone.utc)
        response.end = enddt.astimezone(dtime.timezone.utc)
        response.isopen = details.get("isOpen", bool)

        return response

    ##############
    # Processors #
    ##############
    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> Union[baseRR.PlaceOrderResponseMessage, None]:
        """The function for placing an order with TD Ameritrade."""

        # Check killswitch
        if self.mediator.killswitch is True:
            return None

        # Validate the request
        if request is None:
            logger.error("Order is None")
            raise KeyError("Order is None")

        # Build Request. This is the bare minimum, we could extend the available request parameters in the future
        orderrequest = OrderedDict[str, Any]()
        orderrequest["orderStrategyType"] = request.order.order_strategy_type
        orderrequest["orderType"] = request.order.order_type
        orderrequest["session"] = request.order.session
        orderrequest["duration"] = request.order.duration
        if request.order.price is not None:
            orderrequest["price"] = str(request.order.price)

        legs = []

        for rleg in request.order.legs:
            leg = {
                "instruction": rleg.instruction,
                "quantity": rleg.quantity,
                "instrument": {
                    "assetType": rleg.asset_type,
                    "symbol": rleg.symbol,
                },
            }

            legs.append(leg)

        orderrequest["orderLegCollection"] = legs

        response = baseRR.PlaceOrderResponseMessage()

        # Log the Order
        logger.info(f"Your order being placed is: {orderrequest} ")

        # Place the Order
        try:
            orderresponse = self.getsession().place_order(
                account=self.account_number, order=orderrequest
            )
            logger.info(f'Order {orderresponse["order_id"]} Placed')
        except Exception:
            logger.exception("Failed to place order.")
            return None

        response.order_id = orderresponse.get("order_id")

        # Return the Order ID
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
    ) -> Union[baseRR.CancelOrderResponseMessage, None]:
        """Cancels a given order ID."""

        # Check killswitch
        if self.mediator.killswitch is True:
            return None

        try:
            cancelresponse = self.getsession().cancel_order(
                account=self.account_number,
                order_id=str(request.orderid),
            )
        except Exception:
            logger.exception(f"Failed to cancel order {str(request.orderid)}.")
            return None

        response = baseRR.CancelOrderResponseMessage()
        response.responsecode = cancelresponse.get("status_code")

        return response

    def process_session_hours(
        self, sessionhours: dict, details: dict
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Iterates session hours to build a market hours response"""
        for session, markethours in sessionhours.items():
            if session == "regularMarket":
                response = self.build_market_hours_response(markethours, details)
        return response

    ###############
    # Translators #
    ###############
    def translate_option_chain(
        self,
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
                    if detail.get("settlementType", str) == "P":
                        strikeresponse = self.Build_Option_Chain_Strike(detail)

                        expiry.strikes[
                            detail.get("strikePrice", float)
                        ] = strikeresponse

            response.append(expiry)

        return response

    @staticmethod
    def Build_Option_Chain_Strike(detail: dict):
        strikeresponse = baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike()
        strikeresponse.strike = detail.get("strikePrice", float)
        strikeresponse.multiplier = detail.get("multiplier", float)
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

        return strikeresponse

    def translate_account_order_activity(
        self, order_activity: dict
    ) -> baseModels.OrderActivity:
        """Transforms a TDA order activity dictionary into a LoopTrader order leg"""
        account_order_activity = baseModels.OrderActivity()

        account_order_activity.id = None
        account_order_activity.activity_type = order_activity.get("activityType", "")
        account_order_activity.execution_type = order_activity.get("executionType", "")
        account_order_activity.quantity = order_activity.get("quantity", 0)
        account_order_activity.order_remaining_quantity = order_activity.get(
            "orderRemainingQuantity", 0
        )

        legs = order_activity.get("executionLegs")
        if legs is not None:
            for leg in legs:
                # Build Leg
                accountorderleg = self.translate_account_order_execution_leg(leg)
                # Append Leg
                account_order_activity.execution_legs.append(accountorderleg)

        return account_order_activity

    @staticmethod
    def translate_account_order_execution_leg(leg: dict) -> baseModels.ExecutionLeg:
        """Transforms a TDA order execution leg dictionary into a LoopTrader order leg"""
        account_order_activity = baseModels.ExecutionLeg()

        account_order_activity.id = None
        account_order_activity.leg_id = leg.get("legId", 0)
        account_order_activity.mismarked_quantity = leg.get("mismarkedQuantity", 0)
        account_order_activity.price = leg.get("price", 0.0)
        account_order_activity.quantity = leg.get("quantity", 0)
        account_order_activity.time = dtime.datetime.strptime(
            leg.get("time", dtime.datetime), DT_REGEX
        )

        return account_order_activity

    @staticmethod
    def translate_account_order_leg(leg: dict) -> baseModels.OrderLeg:
        """Transforms a TDA order leg dictionary into a LoopTrader order leg"""
        accountorderleg = baseModels.OrderLeg()
        accountorderleg.leg_id = leg.get("legId", 0)
        accountorderleg.instruction = leg.get("instruction", "")
        accountorderleg.position_effect = leg.get("positionEffect", "")
        accountorderleg.quantity = leg.get("quantity", 0)

        instrument = leg.get("instrument")

        if instrument is not None:
            accountorderleg.cusip = instrument.get("cusip", None)
            accountorderleg.symbol = instrument.get("symbol", None)
            accountorderleg.description = instrument.get("description", None)
            accountorderleg.asset_type = leg.get("assetType", "")

            if accountorderleg.description is not None:
                match = re.search(
                    r"([A-Z]{1}[a-z]{2} \d{1,2} \d{4})", accountorderleg.description
                )
                if match is not None:
                    dt = dtime.datetime.strptime(match.group(), "%b %d %Y")
                    accountorderleg.expiration_date = dt.date()

            accountorderleg.put_call = instrument.get("putCall", None)
        return accountorderleg

    def translate_account_order(self, order: dict) -> baseModels.Order:
        """Transforms a TDA order dictionary into a LoopTrader order"""

        if order is None:
            raise ValueError("No Order Passed In")

        accountorder = self.translate_base_account_order(order)

        legs = order.get("orderLegCollection")
        if legs is not None:
            for leg in legs:
                # Build Leg
                accountorderleg = self.translate_account_order_leg(leg)
                accountorderleg.order_id = accountorder.order_id
                # Append Leg
                accountorder.legs.append(accountorderleg)

        activities = order.get("orderActivityCollection")
        if activities is not None:
            for activity in activities:
                # Build Leg
                accountorderactivity = self.translate_account_order_activity(activity)
                accountorderactivity.order_id = accountorder.order_id

                # Append Leg
                accountorder.activities.append(accountorderactivity)

        return accountorder

    @staticmethod
    def translate_base_account_order(order) -> baseModels.Order:
        if order is None:
            raise ValueError("No Order to Translate")

        accountorder = baseModels.Order()
        accountorder.order_strategy_type = order.get("complexOrderStrategyType", "")
        accountorder.order_type = order.get("orderType", "")
        accountorder.remaining_quantity = order.get("remainingQuantity", 0)
        accountorder.requested_destination = order.get("requestedDestination", "")
        accountorder.session = order.get("session", "")
        accountorder.duration = order.get("duration", "")
        accountorder.quantity = order.get("quantity", 0)
        accountorder.filled_quantity = order.get("filledQuantity", 0)
        accountorder.price = order.get("price", 0.0)
        accountorder.order_id = order.get("orderId", 0)
        accountorder.status = order.get("status", "")
        accountorder.entered_time = dtime.datetime.strptime(
            order.get("enteredTime", dtime.datetime), DT_REGEX
        )

        close = order.get("closeTime")
        if close is not None:
            accountorder.close_time = dtime.datetime.strptime(close, DT_REGEX)
        accountorder.account_id = order.get("accountId", 0)
        accountorder.cancelable = order.get("cancelable", False)
        accountorder.editable = order.get("editable", False)
        accountorder.legs = []
        return accountorder

    @staticmethod
    def translate_account_position(position: dict):
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
        accountposition.strikeprice = 1

        instrument = position.get("instrument", dict)

        if instrument is not None:
            TdaBroker.translate_account_position_instrument(accountposition, instrument)

        return accountposition

    @staticmethod
    def translate_account_position_instrument(
        accountposition: baseRR.AccountPosition, instrument: dict
    ):
        """Translates an instrument into an account position

        Args:
            accountposition (baseRR.AccountPosition): Account Position to build
            instrument (baseRR.Instrument): Instrument to translate
        """
        # Get the symbol
        symbol = instrument.get("symbol", str)

        accountposition.assettype = instrument.get("assetType", str)

        # If we have a symbol, try to extract an expiration date
        if symbol is not None:
            # Set the symbol
            accountposition.symbol = symbol

            # Get our regex match
            exp_match = re.search(r"(\d{6})(?=[PC])", symbol)

            # If we have a match, try to StrpTime
            if exp_match is not None:
                accountposition.expirationdate = dtime.datetime.strptime(
                    exp_match.group(), "%m%d%y"
                )

            strike_match = re.search(r"(?<=[PC])\d\w+", symbol)

            if strike_match is not None:
                accountposition.strikeprice = float(strike_match.group())
            elif accountposition.assettype == "OPTION":
                logger.error(f"No strike price found for {symbol}")

        # Map the other fields
        accountposition.description = instrument.get("description", str)
        accountposition.putcall = instrument.get("putCall", str)
        accountposition.underlyingsymbol = instrument.get("underlyingSymbol", str)
