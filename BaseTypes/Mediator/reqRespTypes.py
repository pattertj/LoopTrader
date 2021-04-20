from dataclasses import dataclass, field
from datetime import date, datetime

import attr


@attr.s(auto_attribs=True)
class PlaceOrderRequestMessage():
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    orderstrategytype: str = attr.ib(validator=attr.validators.in_(['SINGLE', 'OCO', 'TRIGGER']))
    duration: str = attr.ib(validator=attr.validators.in_(['DAY', 'GOOD_TILL_CANCEL', 'FILL_OR_KILL']))
    assettype: str = attr.ib(validator=attr.validators.in_(['EQUITY', 'OPTION', 'INDEX', 'MUTUAL_FUND', 'CASH_EQUIVALENT', 'FIXED_INCOME', 'CURRENCY']))
    instruction: str = attr.ib(validator=attr.validators.in_(['BUY', 'SELL', 'BUY_TO_COVER', 'SELL_SHORT', 'BUY_TO_OPEN', 'BUY_TO_CLOSE', 'SELL_TO_OPEN', 'SELL_TO_CLOSE', 'EXCHANGE']))
    ordertype: str = attr.ib(validator=attr.validators.in_(['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP', 'MARKET_ON_CLOSE', 'EXERCISE', 'TRAILING_STOP_LIMIT', 'NET_DEBIT', 'NET_CREDIT', 'NET_ZERO']))
    ordersession: str = attr.ib(validator=attr.validators.in_(['NORMAL', 'AM', 'PM', 'SEAMLESS']))
    positioneffect: str = attr.ib(validator=attr.validators.in_(['OPENING', 'CLOSING', 'AUTOMATIC']))


@attr.s(auto_attribs=True, init=False)
class PlaceOrderResponseMessage():
    orderid: int


@attr.s(auto_attribs=True)
class GetOptionChainRequestMessage():
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    contracttype: str = attr.ib(validator=attr.validators.in_(['CALL', 'PUT', 'ALL']))
    includequotes: bool = attr.ib(validator=attr.validators.instance_of(bool))
    optionrange: str = attr.ib(validator=attr.validators.in_(['ITM', 'NTM', 'OTM', 'SAK', 'SBK', 'SNK', 'ALL']))
    fromdate: date = attr.ib(validator=attr.validators.instance_of(date))
    todate: date = attr.ib(validator=attr.validators.instance_of(date))


@attr.s(auto_attribs=True, init=False)
class GetOptionChainResponseMessage():
    # Define Expiration Date Object
    @attr.s(auto_attribs=True, init=False)
    class ExpirationDate():

        # Define Strike Object
        @attr.s(auto_attribs=True, init=False)
        class Strike():
            strike: float
            bid: float
            ask: float
            delta: float
            gamma: float
            theta: float
            vega: float
            rho: float
            symbol: str
            description: str
            putcall: str = attr.ib(validator=attr.validators.in_(['CALL', 'PUT']))
            settlementtype: str
            expirationtype: str

        expirationdate: datetime
        daystoexpiration: int
        strikes: list[Strike]

    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    underlyinglastprice: float = attr.ib(validator=attr.validators.instance_of(float))
    volatility: float = attr.ib(validator=attr.validators.instance_of(float))
    putexpdatemap: list[ExpirationDate]
    callexpdatemap: list[ExpirationDate]


@dataclass
class GetAccountRequestMessage():
    orders: bool
    positions: bool


@dataclass(init=False)
class AccountPosition():
    shortquantity: int
    averageprice: float
    longquantity: int
    assettype: str
    symbol: str
    description: str
    putcall: str
    underlyingsymbol: str
    expirationdate: datetime


@dataclass(init=False)
class AccountOrderLeg():
    legid: int
    orders: bool
    cusip: str
    symbol: str
    description: str
    instruction: str
    positioneffect: str
    quantity: int
    putcall: str


@dataclass(init=False)
class AccountOrder():
    duration: str
    quantity: int
    filledquantity: int
    price: float
    orderid: str
    status: str
    enteredtime: datetime
    closetime: datetime
    accountid: int
    cancelable: bool
    editable: bool
    legs: list[AccountOrderLeg] = field(default_factory=list)


@dataclass(init=False)
class AccountBalance():
    liquidationvalue: float
    buyingpower: float


@dataclass(init=False)
class GetAccountResponseMessage():
    currentbalances: AccountBalance
    positions: list[AccountPosition] = field(default_factory=list)
    orders: list[AccountOrder] = field(default_factory=list)


@dataclass
class CancelOrderRequestMessage():
    orderid: int


@dataclass(init=False)
class CancelOrderResponseMessage():
    responsecode: str


@dataclass
class GetOrderRequestMessage():
    orderid: int


@dataclass(init=False)
class GetOrderResponseMessage():
    orderid: int
    status: str
    accountid: int
    enteredtime: datetime
    closetime: datetime
    instruction: str
    symbol: str
    description: str
    positioneffect: str


@attr.s(auto_attribs=True)
class GetMarketHoursRequestMessage():
    markets: list[str] = attr.ib(validator=attr.validators.deep_iterable(member_validator=attr.validators.in_(['OPTION', 'EQUITY', 'FUTURE', 'FOREX', 'BOND']), iterable_validator=attr.validators.instance_of(list)))
    datetime: datetime = datetime.now()


@attr.s(auto_attribs=True, init=False)
class GetMarketHoursResponseMessage():
    # Define Product Object
    @attr.s(auto_attribs=True, init=False)
    class Product():

        # Define Session Object
        @attr.s(auto_attribs=True, init=False)
        class Session():
            session: str
            start: datetime
            end: datetime

        product: str
        productname: str
        sessions: list[Session]

    markettype: str
    products: list[Product]


@dataclass
class SendNotificationRequestMessage():
    message: str


@dataclass
class SetKillSwitchRequestMessage():
    kill_switch: bool
