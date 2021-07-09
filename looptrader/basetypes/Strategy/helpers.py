import datetime as dt
import logging
import logging.config
import math
from typing import Tuple, Union
from urllib.request import urlopen
from xml.etree.ElementTree import parse

import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Mediator.abstractMediator import Mediator
from py_vollib.black.greeks.analytical import delta
from py_vollib.black.implied_volatility import implied_volatility

logger = logging.getLogger("autotrader")


##############################
### Notification Functions ###
##############################
def send_notification(mediator: Mediator, message: str):
    # Build Request
    notification = baseRR.SendNotificationRequestMessage(message)

    # Send notification
    mediator.send_notification(notification)


####################
### DB Functions ###
####################
def get_db_positions(mediator: Mediator, strategy_id: int):
    # Build Request
    request = baseRR.ReadOpenPositionsByStrategyIDRequest(strategy_id)

    # Create Order
    return mediator.read_open_db_position_by_strategy_id(request)


def get_db_orders(mediator: Mediator, position_id: int):
    # Build Request
    request = baseRR.ReadOrdersByPositionIDRequest(position_id)

    # Create Order
    return mediator.read_orders_by_position_id(request)


def close_db_order(mediator: Mediator, order_id: int):
    pass


def close_db_position(mediator: Mediator, position_id: int):
    pass


def create_db_order(mediator: Mediator, order_id: int, strategy_id: int):
    # Build Request
    request = baseRR.CreateDatabaseOrderRequest(order_id, strategy_id, "NEW")

    # Create Order
    mediator.create_db_order(request)


def create_db_position(
    mediator: Mediator,
    strategy_id: int,
    symbol: str,
    quantity: int,
    opening_order_id: int,
):
    # Build Request
    request = baseRR.CreateDatabasePositionRequest(
        strategy_id, symbol, quantity, True, opening_order_id, 0
    )

    # Create Order
    mediator.create_db_position(request)


def cancel_db_order(self, mediator: Mediator, order_id: int):
    pass


########################
### Broker Functions ###
########################
def place_order(
    mediator: Mediator, request: baseRR.PlaceOrderRequestMessage
) -> Union[baseRR.PlaceOrderResponseMessage, None]:
    # Get Order
    return mediator.place_order(request)


def cancel_broker_order(mediator: Mediator, orderid: int, strategy_name: str) -> bool:
    # Build Request
    request = baseRR.CancelOrderRequestMessage(strategy_name, int(orderid))

    # Cancel Order
    response = mediator.cancel_order(request)

    # Handle Response
    if response is None:
        logger.error("Cancel Order Failed.")
        return False

    if response.responsecode == "200":
        return True

    logger.error("Cancel Order Failed. Code {}".format(response.responsecode))
    return False


def get_account(
    mediator: Mediator, strategy_name: str, get_orders: bool, get_positions: bool
) -> Union[baseRR.GetAccountResponseMessage, None]:
    # Build Request
    request = baseRR.GetAccountRequestMessage(strategy_name, get_orders, get_positions)

    # Get Market Hours
    return mediator.get_account(request)


def get_market_hours(
    mediator: Mediator, date: dt.datetime, strategy_name: str
) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
    # Build Request
    request = baseRR.GetMarketHoursRequestMessage(
        strategy_name, market="OPTION", product="IND", datetime=date
    )

    # Get Market Hours
    return mediator.get_market_hours(request)


def get_next_market_hours(
    mediator: Mediator,
    strategy_name: str,
    date: dt.datetime = dt.datetime.now().astimezone(dt.timezone.utc),
):
    hours = get_market_hours(mediator, date, strategy_name)

    if hours is None or hours.close < dt.datetime.now().astimezone(dt.timezone.utc):
        return get_next_market_hours(
            mediator, strategy_name, date + dt.timedelta(days=1)
        )

    return hours


def get_order(
    mediator: Mediator, order_id: int, strategy_name: str
) -> Union[baseRR.GetOrderResponseMessage, None]:
    # Build Request
    request = baseRR.GetOrderRequestMessage(strategy_name, order_id)

    # Get Order
    return mediator.get_order(request)


def get_option_chain(
    mediator: Mediator,
    strategy_name: str,
    put_or_call: str,
    min_dte: int,
    max_dte: int,
    underlying: str,
) -> Union[baseRR.GetOptionChainResponseMessage, None]:
    # Build Request
    request = baseRR.GetOptionChainRequestMessage(
        strategy_name,
        contracttype=put_or_call,
        fromdate=dt.date.today() + dt.timedelta(days=min_dte),
        todate=dt.date.today() + dt.timedelta(days=max_dte),
        symbol=underlying,
        includequotes=False,
        optionrange="ALL",
    )

    # Get Option Chain
    return mediator.get_option_chain(request)


################################
### General Helper Functions ###
################################
def format_order_price(price: float, base: float) -> float:
    """Formats a price according to brokerage rules."""
    logger.debug("format_order_price")

    return truncate(base * round(price / base), 2)


def truncate(number: float, digits: int) -> float:
    """Truncates a float to a specified number of digits."""
    logger.debug("truncate")
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


def get_risk_free_rate():
    # Get the latest feed from the FED
    sFedURL = "https://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$top=1&$orderby=NEW_DATE%20desc"

    # Open the url
    oResponse = urlopen(sFedURL)

    # Parse the XML
    tree = parse(oResponse)
    # tree.getroot()

    # Build the xpath query tot he 3 month interest rate
    xPathQuery = (
        "{http://www.w3.org/2005/Atom}entry/"
        "{http://www.w3.org/2005/Atom}content/"
        "{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/"
        "{http://schemas.microsoft.com/ado/2007/08/dataservices}BC_3MONTH"
    )

    # Execute the xPath
    oNode = tree.findall(xPathQuery)

    return float(oNode[0].text)


def calculate_iv(
    option_price: float,
    underlying_price: float,
    strike: float,
    risk_free_rate: float,
    time_in_days: float,
    put_or_call: str,
) -> float:
    # Set Variables
    risk_free_rate = get_risk_free_rate() if risk_free_rate is None else risk_free_rate
    flag = "p" if put_or_call == "PUT" else "c"
    time_in_years = time_in_days / 365

    # Calculate IV
    return implied_volatility(
        option_price, underlying_price, strike, risk_free_rate, time_in_years, flag
    )


def calculate_delta(
    underlying_price: float,
    strike: float,
    risk_free_rate: float,
    time_in_days: float,
    put_or_call: str,
    iv: float,
) -> float:
    """Calculates the Delta using py_vollib.black

    Args:
        underlying_price (float): Price of the Underlying
        strike (float): Strike Price
        risk_free_rate (float): Risk-Free Rate of Return
        time_in_days (float): Days to Expiration
        put_or_call (str): 'PUT' or 'CALL'
        iv (float): Implied volatility

    Returns:
        float: The Option's Delta
    """
    # Set Variables
    flag = "p" if put_or_call == "PUT" else "c"
    time_in_years = time_in_days / 365

    return delta(flag, underlying_price, strike, time_in_years, risk_free_rate, iv)


def get_next_expiration(
    chain: baseRR.GetOptionChainResponseMessage, put_or_call: str
) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate, None]:
    """Checks an option chain response for the next expiration date.

    Args:
        chain (baseRR.GetOptionChainResponseMessage): The option chain to search
        put_or_call (str): 'PUT' or 'CALL'

    Returns:
        Union[baseRR.GetOptionChainResponseMessage.ExpirationDate, None]: The selected expiration date for the option chain provided.
    """
    logger.debug("get_next_expiration")

    if chain is None:
        logger.error("No option chain provided.")
        return None

    if put_or_call == "PUT":
        if chain.putexpdatemap is None:
            logger.error("No put strikes provided.")
            return None

        return min(chain.putexpdatemap, key=lambda x: x.daystoexpiration)
    else:
        if chain.callexpdatemap is None:
            logger.error("No call strikes provided.")
            return None

        return min(chain.callexpdatemap, key=lambda x: x.daystoexpiration)


def get_best_strike_by_delta(
    strikes: dict[float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike],
    min_delta: float,
    max_delta: float,
    buying_power: float,
    max_loss_percent: float,
) -> Tuple[
    Union[None, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike], int, float
]:
    """Returns the strike providing the maximum total premium bewteen the given deltas, based on the quantity calculated using buying_power and max_loss_percent.

    Args:
        strikes (ValuesView[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike]): List of strikes to search.
        min_delta (float): Minimum delta to consider
        max_delta (float): Maximum delta to consider
        buying_power (float): Buying Power available for the trade
        max_loss_percent (float): Max loss percentages

    Returns:
        Tuple[Union[None, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike], int, float]: Tuple containing the Strike, quantity, and mid-price.
    """

    best_mid_price = 0.0
    best_quantity = 0
    best_strike = None
    best_total_premium = 0.0

    for strike in strikes.items():
        if min_delta <= strike[1].delta <= max_delta:
            mid_price = (strike[1].bid + strike[1].ask) / 2
            quantity = int(buying_power // (strike[0] * 100 * float(max_loss_percent)))
            total_premium = mid_price * quantity
            if total_premium > best_total_premium:
                best_mid_price = mid_price
                best_quantity = quantity
                best_total_premium = total_premium
                best_strike = strike[1]

    return (best_strike, best_quantity, best_mid_price)


def build_single_order_request(
    strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
    qty: int,
    price: float,
    buy_or_sell: str,
    open_or_close: str,
    strategy_name: str,
) -> baseRR.PlaceOrderRequestMessage:
    """Builds a good till cancel, limit priced, Order Request Message for a single strike option trade.

    Args:
        strike (baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike): the Strike to trade
        qty (int): The number of contracts
        price (float): The price limit
        buy_or_sell (str): 'BUY' or 'SELL"
        open_or_close (str): 'OPEN' or 'CLOSE'
        strategy_name (str): Name of the strategy being traded.

    Returns:
        baseRR.PlaceOrderRequestMessage: Order Request Message
    """

    # Build Leg
    leg = baseRR.PlaceOrderRequestMessage.Leg()
    leg.symbol = strike.symbol
    leg.assettype = "OPTION"
    leg.quantity = qty

    # Build Order
    orderrequest = baseRR.PlaceOrderRequestMessage()
    orderrequest.strategy_name = strategy_name
    orderrequest.orderstrategytype = "SINGLE"
    orderrequest.duration = "GOOD_TILL_CANCEL"
    orderrequest.ordertype = "LIMIT"
    orderrequest.ordersession = "NORMAL"
    orderrequest.price = price

    # Populate logic fields
    if open_or_close == "OPEN":
        leg.instruction = "SELL_TO_OPEN" if buy_or_sell == "SELL" else "BUY_TO_OPEN"
        orderrequest.positioneffect = "OPENING"
    else:
        leg.instruction = "BUY_TO_CLOSE" if buy_or_sell == "SELL" else "SELL_TO_CLOSE"
        orderrequest.positioneffect = "CLOSING"

    # Assemble
    orderrequest.legs = list[baseRR.PlaceOrderRequestMessage.Leg]()
    orderrequest.legs.append(leg)

    # Return request
    return orderrequest
