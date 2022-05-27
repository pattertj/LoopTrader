from datetime import date, datetime

import attr
import basetypes.Mediator.baseModels as base


@attr.s(auto_attribs=True, init=False)
class PlaceOrderRequestMessage:
    """Generic request object for placing an order."""

    order: base.Order = attr.ib(validator=attr.validators.instance_of(base.Order))


@attr.s(auto_attribs=True, init=False)
class PlaceOrderResponseMessage:
    """Generic response object for placing an order."""

    order_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True)
class GetOptionChainRequestMessage:
    """Generic request object for retrieving the Option Chain."""

    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
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

    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
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
    orders: list[base.Order] = attr.ib(
        validator=attr.validators.instance_of(list[base.Order])
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

    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class CancelOrderResponseMessage:
    """Generic response object for cancelling an order."""

    responsecode: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class GetOrderRequestMessage:
    """Generic request object for reading an order."""

    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class GetOrderResponseMessage:
    """Generic response object for reading an order."""

    order: base.Order = attr.ib(validator=attr.validators.instance_of(base.Order))


@attr.s(auto_attribs=True)
class GetMarketHoursRequestMessage:
    """Generic request object for getting Market Hours."""

    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
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


###################
# Create Strategy #
###################
@attr.s(auto_attribs=True)
class CreateDatabaseStrategyRequest:
    strategy: base.Strategy = attr.ib(
        validator=attr.validators.instance_of(base.Strategy)
    )


@attr.s(auto_attribs=True, init=False)
class CreateDatabaseStrategyResponse:
    id: int = attr.ib(validator=attr.validators.instance_of(int))


################
# Create Order #
################
@attr.s(auto_attribs=True)
class CreateDatabaseOrderRequest:
    order: base.Order = attr.ib(validator=attr.validators.instance_of(base.Order))


@attr.s(auto_attribs=True, init=False)
class CreateDatabaseOrderResponse:
    id: int = attr.ib(validator=attr.validators.instance_of(int))


################
# Update Order #
################
@attr.s(auto_attribs=True)
class UpdateDatabaseOrderRequest:
    order: base.Order = attr.ib(validator=attr.validators.instance_of(base.Order))


@attr.s(auto_attribs=True, init=False)
class UpdateDatabaseOrderResponse:
    id: int = attr.ib(validator=attr.validators.instance_of(int))


##################
# Read by Status #
##################
@attr.s(auto_attribs=True)
class ReadDatabaseStrategyByNameRequest:
    name: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True, init=False)
class ReadDatabaseStrategyByNameResponse:
    strategy: base.Strategy = attr.ib(
        validator=attr.validators.instance_of(base.Strategy)
    )


@attr.s(auto_attribs=True)
class ReadDatabaseOrdersByStatusRequest:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
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


@attr.s(auto_attribs=True, init=False)
class ReadDatabaseOrdersByStatusResponse:
    orders: list[base.Order] = attr.ib(
        validator=attr.validators.instance_of(list[base.Order])
    )


@attr.s(auto_attribs=True)
class ReadOpenDatabaseOrdersRequest:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class ReadOpenDatabaseOrdersResponse:
    orders: list[base.Order] = attr.ib(
        validator=attr.validators.instance_of(list[base.Order])
    )


@attr.s(auto_attribs=True)
class ReadOffsetLegsByExpirationRequest:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    put_or_call: str = attr.ib(validator=attr.validators.instance_of(str))
    expiration: datetime = attr.ib(validator=attr.validators.instance_of(datetime))


@attr.s(auto_attribs=True, init=False)
class ReadOffsetLegsByExpirationResponse:
    offset_legs: list[base.OrderLeg] = attr.ib(
        validator=attr.validators.instance_of(list[base.OrderLeg])
    )


@attr.s(auto_attribs=True)
class GetQuoteRequestMessage:
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
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
    instruments: list[Instrument] = attr.ib(
        validator=attr.validators.instance_of(list[Instrument])
    )
