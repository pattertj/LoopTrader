from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlaceOrderRequestMessage():
    price: float
    quantity: int
    symbol: str
    orderstrategytype: str = "SINGLE"
    duration: str = "GOOD_TILL_CANCEL"
    assettype: str = "OPTION"
    instruction: str = "SELL_TO_OPEN"
    ordertype: str = "LIMIT"
    ordersession: str = "NORMAL"


@dataclass(init=False)
class PlaceOrderResponseMessage():
    orderid: int


@dataclass
class GetOptionChainRequestMessage():
    symbol: str
    contracttype: str
    includequotes: bool
    optionrange: str
    fromdate: datetime
    todate: datetime


@dataclass(init=False)
class GetOptionChainResponseMessage():
    symbol: str
    status: str
    underlyinglastprice: float
    putexpdatemap: dict
    callexpdatemap: dict


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


@dataclass(init=False)
class AccountOrder():
    orders: bool


@dataclass(init=False)
class AccountBalance():
    liquidationvalue: float
    buyingpower: float


@dataclass(init=False)
class GetAccountResponseMessage():
    currentbalances: AccountBalance
    positions: list = field(default_factory=list)
    orders: list = field(default_factory=list)


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


@dataclass
class GetMarketHoursRequestMessage():
    markets: list[str]
    datetime: datetime = datetime.now()


@dataclass(init=False)
class GetMarketHoursResponseMessage():
    isopen: bool
    start: datetime
    end: datetime
