from datetime import date, datetime

import attr


@attr.s(auto_attribs=True, init=False)
class DBCreateStrategyRequestMessage():
    strategy_class: bool = attr.ib(validator=attr.validators.instance_of(bool))
    name: bool = attr.ib(validator=attr.validators.instance_of(bool))
    underlying: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True, init=False)
class DBCreateStrategyResponseMessage():
    result: bool


@attr.s(auto_attribs=True, init=False)
class DBCreateOrderRequestMessage():
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class DBCreateOrderResponseMessage():
    result: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True, init=False)
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
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


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
            strike: float = attr.ib(validator=attr.validators.instance_of(float))
            bid: float = attr.ib(validator=attr.validators.instance_of(float))
            ask: float = attr.ib(validator=attr.validators.instance_of(float))
            delta: float = attr.ib(validator=attr.validators.instance_of(float))
            gamma: float = attr.ib(validator=attr.validators.instance_of(float))
            theta: float = attr.ib(validator=attr.validators.instance_of(float))
            vega: float = attr.ib(validator=attr.validators.instance_of(float))
            rho: float = attr.ib(validator=attr.validators.instance_of(float))
            symbol: str = attr.ib(validator=attr.validators.instance_of(str))
            description: str = attr.ib(validator=attr.validators.instance_of(str))
            putcall: str = attr.ib(validator=attr.validators.in_(['CALL', 'PUT']))
            # TODO: Change to IN
            settlementtype: str = attr.ib(validator=attr.validators.instance_of(str))
            expirationtype: str = attr.ib(validator=attr.validators.instance_of(str))

        expirationdate: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
        daystoexpiration: int = attr.ib(validator=attr.validators.instance_of(int))
        strikes: dict[float, Strike] = attr.ib(validator=attr.validators.instance_of(dict[float, Strike]))

    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    underlyinglastprice: float = attr.ib(validator=attr.validators.instance_of(float))
    volatility: float = attr.ib(validator=attr.validators.instance_of(float))
    putexpdatemap: list[ExpirationDate] = attr.ib(validator=attr.validators.instance_of(list[ExpirationDate]))
    callexpdatemap: list[ExpirationDate] = attr.ib(validator=attr.validators.instance_of(list[ExpirationDate]))


@attr.s(auto_attribs=True)
class GetAccountRequestMessage():
    orders: bool = attr.ib(validator=attr.validators.instance_of(bool))
    positions: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True, init=False)
class AccountPosition():
    shortquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    averageprice: float = attr.ib(validator=attr.validators.instance_of(float))
    longquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    assettype: str = attr.ib(validator=attr.validators.in_(['EQUITY', 'OPTION', 'INDEX', 'MUTUAL_FUND', 'CASH_EQUIVALENT', 'FIXED_INCOME', 'CURRENCY']))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    putcall: str = attr.ib(validator=attr.validators.in_(['CALL', 'PUT']))
    underlyingsymbol: str = attr.ib(validator=attr.validators.instance_of(str))
    expirationdate: datetime = attr.ib(validator=attr.validators.instance_of(datetime))


@attr.s(auto_attribs=True, init=False)
class AccountOrderLeg():
    legid: int = attr.ib(validator=attr.validators.instance_of(int))
    orders: bool = attr.ib(validator=attr.validators.instance_of(bool))
    cusip: str = attr.ib(validator=attr.validators.instance_of(str))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    instruction: str = attr.ib(validator=attr.validators.in_(['BUY', 'SELL', 'BUY_TO_COVER', 'SELL_SHORT', 'BUY_TO_OPEN', 'BUY_TO_CLOSE', 'SELL_TO_OPEN', 'SELL_TO_CLOSE', 'EXCHANGE']))
    positioneffect: str = attr.ib(validator=attr.validators.in_(['OPENING', 'CLOSING', 'AUTOMATIC']))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    putcall: str = attr.ib(validator=attr.validators.in_(['CALL', 'PUT']))


@attr.s(auto_attribs=True, init=False)
class AccountOrder():
    duration: str = attr.ib(validator=attr.validators.in_(['DAY', 'GOOD_TILL_CANCEL', 'FILL_OR_KILL']))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    filledquantity: int = attr.ib(validator=attr.validators.instance_of(int))
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    orderid: str = attr.ib(validator=attr.validators.instance_of(str))
    # TODO: Change to IN
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    enteredtime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    closetime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    accountid: int = attr.ib(validator=attr.validators.instance_of(int))
    cancelable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    editable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    legs: list[AccountOrderLeg] = attr.ib(validator=attr.validators.instance_of(list[AccountOrderLeg]))


@attr.s(auto_attribs=True, init=False)
class AccountBalance():
    liquidationvalue: float = attr.ib(validator=attr.validators.instance_of(float))
    buyingpower: float = attr.ib(validator=attr.validators.instance_of(float))


@attr.s(auto_attribs=True, init=False)
class GetAccountResponseMessage():
    currentbalances: AccountBalance = attr.ib(validator=attr.validators.instance_of(AccountBalance))
    positions: list[AccountPosition] = attr.ib(validator=attr.validators.instance_of(list[AccountPosition]))
    orders: list[AccountOrder] = attr.ib(validator=attr.validators.instance_of(list[AccountOrder]))


@attr.s(auto_attribs=True)
class CancelOrderRequestMessage():
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class CancelOrderResponseMessage():
    responsecode: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class GetOrderRequestMessage():
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class GetOrderResponseMessage():
    orderid: int = attr.ib(validator=attr.validators.instance_of(int))
    # TODO: Change to IN
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    accountid: int = attr.ib(validator=attr.validators.instance_of(int))
    enteredtime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    closetime: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    instruction: str = attr.ib(validator=attr.validators.in_(['BUY', 'SELL', 'BUY_TO_COVER', 'SELL_SHORT', 'BUY_TO_OPEN', 'BUY_TO_CLOSE', 'SELL_TO_OPEN', 'SELL_TO_CLOSE', 'EXCHANGE']))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    positioneffect: str = attr.ib(validator=attr.validators.in_(['OPENING', 'CLOSING', 'AUTOMATIC']))


@attr.s(auto_attribs=True)
class GetMarketHoursRequestMessage():
    market: str = attr.ib(validator=attr.validators.in_(['OPTION', 'EQUITY', 'FUTURE', 'FOREX', 'BOND']))
    product: str = attr.ib(validator=attr.validators.in_(['EQO', 'IND']))
    datetime: datetime = attr.ib(default=datetime.now(), validator=attr.validators.instance_of(datetime))


@attr.s(auto_attribs=True, init=False)
class GetMarketHoursResponseMessage():
    start: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    end: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    isopen: bool = attr.ib(validator=attr.validators.instance_of(bool))


@attr.s(auto_attribs=True)
class SendNotificationRequestMessage():
    message: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True)
class SetKillSwitchRequestMessage():
    kill_switch: bool = attr.ib(validator=attr.validators.instance_of(bool))
