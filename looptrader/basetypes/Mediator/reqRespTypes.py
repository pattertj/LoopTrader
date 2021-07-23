from datetime import date, datetime

import attr


@attr.s(auto_attribs=True, init=False)
class PlaceOrderRequestMessage:
    """Generic request object for placing an order."""

    # Define Order Request Leg Object
    @attr.s(auto_attribs=True, init=False)
    class Leg:

        quantity: int = attr.ib(validator=attr.validators.instance_of(int))
        symbol: str = attr.ib(validator=attr.validators.instance_of(str))
        assettype: str = attr.ib(
            validator=attr.validators.in_(
                [
                    "EQUITY",
                    "OPTION",
                    "INDEX",
                    "MUTUAL_FUND",
                    "CASH_EQUIVALENT",
                    "FIXED_INCOME",
                    "CURRENCY",
                ]
            )
        )
        instruction: str = attr.ib(
            validator=attr.validators.in_(
                [
                    "BUY",
                    "SELL",
                    "BUY_TO_COVER",
                    "SELL_SHORT",
                    "BUY_TO_OPEN",
                    "BUY_TO_CLOSE",
                    "SELL_TO_OPEN",
                    "SELL_TO_CLOSE",
                    "EXCHANGE",
                ]
            )
        )

    price: float = attr.ib(validator=attr.validators.instance_of(float))
    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    orderstrategytype: str = attr.ib(
        validator=attr.validators.in_(["SINGLE", "OCO", "TRIGGER"])
    )
    duration: str = attr.ib(
        validator=attr.validators.in_(["DAY", "GOOD_TILL_CANCEL", "FILL_OR_KILL"])
    )
    ordertype: str = attr.ib(
        validator=attr.validators.in_(
            [
                "MARKET",
                "LIMIT",
                "STOP",
                "STOP_LIMIT",
                "TRAILING_STOP",
                "MARKET_ON_CLOSE",
                "EXERCISE",
                "TRAILING_STOP_LIMIT",
                "NET_DEBIT",
                "NET_CREDIT",
                "NET_ZERO",
            ]
        )
    )
    ordersession: str = attr.ib(
        validator=attr.validators.in_(["NORMAL", "AM", "PM", "SEAMLESS"])
    )
    positioneffect: str = attr.ib(
        validator=attr.validators.in_(["OPENING", "CLOSING", "AUTOMATIC"])
    )
    legs: list[Leg] = attr.ib(validator=attr.validators.instance_of(list[Leg]))


@attr.s(auto_attribs=True, init=False)
class PlaceOrderResponseMessage:
    """Generic response object for placing an order."""

    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class GetOptionChainRequestMessage:
    """Generic request object for retrieving the Option Chain."""

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    contracttype: str = attr.ib(validator=attr.validators.in_(["CALL", "PUT", "ALL"]))
    includequotes: bool = attr.ib(validator=attr.validators.instance_of(bool))
    optionrange: str = attr.ib(
        validator=attr.validators.in_(["ITM", "NTM", "OTM", "SAK", "SBK", "SNK", "ALL"])
    )
    fromdate: date = attr.ib(validator=attr.validators.instance_of(date))
    todate: date = attr.ib(validator=attr.validators.instance_of(date))


@attr.s(auto_attribs=True, init=False)
class GetOptionChainResponseMessage:
    """Generic response object for retrieving an Option Chain."""

    # Define Expiration Date Object
    @attr.s(auto_attribs=True, init=False)
    class ExpirationDate:

        # Define Strike Object
        @attr.s(auto_attribs=True, init=False)
        class Strike:
            strike: float = attr.ib(validator=attr.validators.instance_of(float))
            multiplier: float = attr.ib(validator=attr.validators.instance_of(float))
            bid: float = attr.ib(validator=attr.validators.instance_of(float))
            ask: float = attr.ib(validator=attr.validators.instance_of(float))
            delta: float = attr.ib(validator=attr.validators.instance_of(float))
            gamma: float = attr.ib(validator=attr.validators.instance_of(float))
            theta: float = attr.ib(validator=attr.validators.instance_of(float))
            vega: float = attr.ib(validator=attr.validators.instance_of(float))
            rho: float = attr.ib(validator=attr.validators.instance_of(float))
            symbol: str = attr.ib(validator=attr.validators.instance_of(str))
            description: str = attr.ib(validator=attr.validators.instance_of(str))
            putcall: str = attr.ib(validator=attr.validators.in_(["CALL", "PUT"]))
            settlementtype: str = attr.ib(validator=attr.validators.instance_of(str))
            expirationtype: str = attr.ib(validator=attr.validators.instance_of(str))

        expirationdate: datetime = attr.ib(
            validator=attr.validators.instance_of(datetime)
        )
        daystoexpiration: int = attr.ib(validator=attr.validators.instance_of(int))
        strikes: dict[float, Strike] = attr.ib(
            validator=attr.validators.instance_of(dict[float, Strike])
        )

    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    underlyinglastprice: float = attr.ib(validator=attr.validators.instance_of(float))
    volatility: float = attr.ib(validator=attr.validators.instance_of(float))
    putexpdatemap: list[ExpirationDate] = attr.ib(
        validator=attr.validators.instance_of(list[ExpirationDate])
    )
    callexpdatemap: list[ExpirationDate] = attr.ib(
        validator=attr.validators.instance_of(list[ExpirationDate])
    )


@attr.s(auto_attribs=True)
class GetAccountRequestMessage:
    """Generic request object for retrieving account details."""

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    orders: bool = attr.ib(validator=attr.validators.instance_of(bool))
    positions: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True)
class GetAllAccountsRequestMessage:
    """Generic request object for retrieving account details."""

    orders: bool = attr.ib(validator=attr.validators.instance_of(bool))
    positions: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True, init=False)
class AccountPosition:
    """Generic object for retrieving position details on an account."""

    shortquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    averageprice: float = attr.ib(validator=attr.validators.instance_of(float))
    strikeprice: float = attr.ib(validator=attr.validators.instance_of(float))
    currentdayprofitloss: float = attr.ib(validator=attr.validators.instance_of(float))
    currentdayprofitlosspercentage: float = attr.ib(
        validator=attr.validators.instance_of(float)
    )
    marketvalue: float = attr.ib(validator=attr.validators.instance_of(float))
    longquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    assettype: str = attr.ib(
        validator=attr.validators.in_(
            [
                "EQUITY",
                "OPTION",
                "INDEX",
                "MUTUAL_FUND",
                "CASH_EQUIVALENT",
                "FIXED_INCOME",
                "CURRENCY",
            ]
        )
    )
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    putcall: str = attr.ib(validator=attr.validators.in_(["CALL", "PUT"]))
    underlyingsymbol: str = attr.ib(validator=attr.validators.instance_of(str))
    expirationdate: datetime = attr.ib(validator=attr.validators.instance_of(datetime))


@attr.s(auto_attribs=True, init=False)
class AccountOrderLeg:
    """Generic object for retrieving order leg details on an account."""

    legid: int = attr.ib(validator=attr.validators.instance_of(int))
    orders: bool = attr.ib(validator=attr.validators.instance_of(bool))
    cusip: str = attr.ib(validator=attr.validators.instance_of(str))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    instruction: str = attr.ib(
        validator=attr.validators.in_(
            [
                "BUY",
                "SELL",
                "BUY_TO_COVER",
                "SELL_SHORT",
                "BUY_TO_OPEN",
                "BUY_TO_CLOSE",
                "SELL_TO_OPEN",
                "SELL_TO_CLOSE",
                "EXCHANGE",
            ]
        )
    )
    positioneffect: str = attr.ib(
        validator=attr.validators.in_(["OPENING", "CLOSING", "AUTOMATIC"])
    )
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    putcall: str = attr.ib(validator=attr.validators.in_(["CALL", "PUT"]))


@attr.s(auto_attribs=True, init=False)
class AccountOrder:
    """Generic object to hold order details for an account."""

    duration: str = attr.ib(
        validator=attr.validators.in_(["DAY", "GOOD_TILL_CANCEL", "FILL_OR_KILL"])
    )
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    filledquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    orderid: str = attr.ib(validator=attr.validators.instance_of(str))
    status: str = attr.ib(
        validator=attr.validators.in_(
            [
                "AWAITING_PARENT_ORDER",
                "AWAITING_CONDITION",
                "AWAITING_MANUAL_REVIEW",
                "ACCEPTED",
                "AWAITING_UR_OUT",
                "PENDING_ACTIVATION",
                "QUEUED",
                "WORKING",
                "REJECTED",
                "PENDING_CANCEL",
                "CANCELED",
                "PENDING_REPLACE",
                "REPLACED",
                "FILLED",
                "EXPIRED",
            ]
        )
    )
    enteredtime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    closetime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    accountid: int = attr.ib(validator=attr.validators.instance_of(int))
    cancelable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    editable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    legs: list[AccountOrderLeg] = attr.ib(
        validator=attr.validators.instance_of(list[AccountOrderLeg])
    )


@attr.s(auto_attribs=True, init=False)
class AccountBalance:
    """Generic object to hold balance details for an account."""

    liquidationvalue: float = attr.ib(validator=attr.validators.instance_of(float))
    buyingpower: float = attr.ib(validator=attr.validators.instance_of(float))


@attr.s(auto_attribs=True, init=False)
class GetAccountResponseMessage:
    """Generic response object for retrieving account details."""

    accountnumber: int = attr.ib(validator=attr.validators.instance_of(int))
    currentbalances: AccountBalance = attr.ib(
        validator=attr.validators.instance_of(AccountBalance)
    )
    positions: list[AccountPosition] = attr.ib(
        validator=attr.validators.instance_of(list[AccountPosition])
    )
    orders: list[AccountOrder] = attr.ib(
        validator=attr.validators.instance_of(list[AccountOrder])
    )


@attr.s(auto_attribs=True, init=False)
class GetAllAccountsResponseMessage:
    """Generic response object for retrieving all account details."""

    accounts: list[GetAccountResponseMessage] = attr.ib(
        validator=attr.validators.instance_of(list[GetAccountResponseMessage])
    )


@attr.s(auto_attribs=True)
class CancelOrderRequestMessage:
    """Generic request object for cancelling an order."""

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class CancelOrderResponseMessage:
    """Generic response object for cancelling an order."""

    responsecode: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class GetOrderRequestMessage:
    """Generic request object for reading an order."""

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class GetOrderResponseMessage:
    """Generic response object for reading an order."""

    orderid: int = attr.ib(validator=attr.validators.instance_of(int))
    status: str = attr.ib(
        validator=attr.validators.in_(
            [
                "AWAITING_PARENT_ORDER",
                "AWAITING_CONDITION",
                "AWAITING_MANUAL_REVIEW",
                "ACCEPTED",
                "AWAITING_UR_OUT",
                "PENDING_ACTIVATION",
                "QUEUED",
                "WORKING",
                "REJECTED",
                "PENDING_CANCEL",
                "CANCELED",
                "PENDING_REPLACE",
                "REPLACED",
                "FILLED",
                "EXPIRED",
            ]
        )
    )
    accountid: int = attr.ib(validator=attr.validators.instance_of(int))
    enteredtime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    closetime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    instruction: str = attr.ib(
        validator=attr.validators.in_(
            [
                "BUY",
                "SELL",
                "BUY_TO_COVER",
                "SELL_SHORT",
                "BUY_TO_OPEN",
                "BUY_TO_CLOSE",
                "SELL_TO_OPEN",
                "SELL_TO_CLOSE",
                "EXCHANGE",
            ]
        )
    )
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    positioneffect: str = attr.ib(
        validator=attr.validators.in_(["OPENING", "CLOSING", "AUTOMATIC"])
    )


@attr.s(auto_attribs=True)
class GetMarketHoursRequestMessage:
    """Generic request object for getting Market Hours."""

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    market: str = attr.ib(
        validator=attr.validators.in_(["OPTION", "EQUITY", "FUTURE", "FOREX", "BOND"])
    )
    product: str = attr.ib(validator=attr.validators.in_(["EQO", "IND"]))
    datetime: datetime = attr.ib(
        default=datetime.now(), validator=attr.validators.instance_of(datetime)
    )


@attr.s(auto_attribs=True, init=False)
class GetMarketHoursResponseMessage:
    """Generic reponse object for getting Market Hours."""

    start: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    end: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    isopen: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True)
class SendNotificationRequestMessage:
    """Generic request object for sending a notification."""

    message: str = attr.ib(validator=attr.validators.instance_of(str))
    parsemode: str = attr.ib(
        default="HTML",
        validator=attr.validators.in_(["Markdown", "MarkdownV2", "HTML"]),
    )


@attr.s(auto_attribs=True)
class SetKillSwitchRequestMessage:
    """Generic request object for setting the bot killswitch."""

    kill_switch: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True)
class CreateDatabaseStrategyRequest:
    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class CreateDatabaseStrategyResponse:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class CreateDatabaseOrderRequest:
    broker_order_number: int = attr.ib(validator=attr.validators.instance_of(int))
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    status: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class CreateDatabaseOrderResponse:
    order_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class CreateDatabasePositionRequest:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    is_open: bool = attr.ib(validator=attr.validators.instance_of(bool))
    entry_order_id: int = attr.ib(validator=attr.validators.instance_of(int))
    exit_order_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class CreateDatabasePositionResponse:
    position_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class ReadOpenPositionsByStrategyIDRequest:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class ReadOpenPositionsByStrategyIDResponse:
    positions: list[AccountPosition] = attr.ib(
        validator=attr.validators.instance_of(list[AccountPosition])
    )


@attr.s(auto_attribs=True)
class GetQuoteRequestMessage:
    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    instruments: list[str] = attr.ib(validator=attr.validators.instance_of(list))


@attr.s(auto_attribs=True, init=False)
class Instrument:
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    bidPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    bidSize: float = attr.ib(validator=attr.validators.instance_of(float))
    askPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    askSize: float = attr.ib(validator=attr.validators.instance_of(float))
    lastPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    openPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    highPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    lowPrice: float = attr.ib(validator=attr.validators.instance_of(float))
    closePrice: float = attr.ib(validator=attr.validators.instance_of(float))
    volatility: float = attr.ib(validator=attr.validators.instance_of(float))


@attr.s(auto_attribs=True, init=False)
class GetQuoteResponseMessage:
    instruments: list[Instrument] = attr.ib(validator=attr.validators.instance_of(list[Instrument]))
