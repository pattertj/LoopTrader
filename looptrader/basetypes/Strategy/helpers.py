import datetime as dt
import logging
import logging.config
import math
from typing import Union

import basetypes.Mediator.reqRespTypes as baseRR
import requests
from basetypes.Mediator.abstractMediator import Mediator
from py_vollib.black.greeks.analytical import delta
from py_vollib.black.implied_volatility import implied_volatility

logger = logging.getLogger("autotrader")


##################
### Formatters ###
##################
def format_order_price(price: float) -> float:
    """Formats a price according to brokerage rules.

    Args:
        price (float): Price to be formatted

    Returns:
        float: Formatted Price
    """
    logger.debug("format_order_price")

    base = 0.1 if price > 3 else 0.05
    return truncate(base * round(price / base), 2)


def truncate(number: float, digits: int) -> float:
    """Truncates a float to a specified number of digits.

    Args:
        number (float): Number to be truncated
        digits (int): Number of digits to truncate to

    Returns:
        float: Truncated number
    """
    logger.debug("truncate")

    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


##############################
### Notification Functions ###
##############################
def send_notification(
    message: str, strategy_name: str, strategy_id: int, mediator: Mediator
):
    """Helper method for sending notification

    Args:
        message (str): Message to be sent.
        strategy_name (str): Strategy Name
        strategy_id (int): Strategy ID Number
        mediator (Mediator): Mediator for the Strategy
    """
    # Append Strategy Prefix
    message = f"Strategy {strategy_name}({strategy_id}): {message}"

    # Build Request
    notification = baseRR.SendNotificationRequestMessage(message)

    # Send notification
    mediator.send_notification(notification)


###############################
### Volatility Calculations ###
###############################
def get_risk_free_rate() -> float:
    now = dt.datetime.now()

    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all/"
        + str(now.year)
        + str(now.strftime("%m"))
        + "?type=daily_treasury_yield_curve"
    )

    r = requests.get(url)

    date_curve = r.text.split("\n")

    for line in date_curve[1:]:
        columns = line.split(",")
        print(float(columns[3]))
        return float(columns[3])

    return 0.0


def calculate_iv(
    option_price: float,
    underlying_price: float,
    strike: float,
    risk_free_rate: Union[float, None],
    time_in_days: float,
    put_or_call: str,
) -> float:
    """Calculates the Volatility of a single option

    Args:
        option_price (float): The option's price
        underlying_price (float): The stock price
        strike (float): The option's strike
        risk_free_rate (float): The Risk-Free rate of return
        time_in_days (float): Days until expiration
        put_or_call (str): "PUT" or "CALL"

    Returns:
        float: The Strike's implied volatility
    """
    if time_in_days == 0:
        raise ValueError("Days to Expiration should be > 0")

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
    iv: Union[float, None],
    option_price: Union[float, None],
) -> float:
    """[summary]

    Args:
        underlying_price (float): Price of the Underlying
        strike (float): Strike Price
        risk_free_rate (float): Risk-Free Rate of Return
        time_in_days (float): Days to Expiration
        put_or_call (str): 'PUT' or 'CALL'
        iv (Union[float, None]): Implied volatility, if not provided, it will be calculated
        option_price (Union[float, None]): If IV is not provided, this is required

    Returns:
        float: [description]
    """
    if time_in_days == 0:
        raise ValueError("Days to Expiration should be > 0")

    # Set Variables
    if iv is None:
        if option_price is None:
            raise KeyError("Option Price is required when IV is None")
        else:
            iv = calculate_iv(
                option_price,
                underlying_price,
                strike,
                risk_free_rate,
                time_in_days,
                put_or_call,
            )

    flag = "p" if put_or_call == "PUT" else "c"
    time_in_years = time_in_days / 365

    return delta(flag, underlying_price, strike, time_in_years, risk_free_rate, iv)
