import logging
import logging.config
import math
from typing import Union
from urllib.request import urlopen
from xml.etree.ElementTree import parse

import basetypes.Mediator.reqRespTypes as baseRR
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
    """Returns the current Risk-Free Rate of Return

    Returns:
        float: Current Risk-Free Rate of Return
    """
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

    if oNode[0].text is None:
        raise ValueError("No Risk Free Rate found.")
    else:
        return float(oNode[0].text)


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
