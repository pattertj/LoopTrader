from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlaceOrderRequestMessage():
    ordertype: str


@dataclass(init=False)
class PlaceOrderResponseMessage():
    ordertype: str


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
    ordertype: str


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
