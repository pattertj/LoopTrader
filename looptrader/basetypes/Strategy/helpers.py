import datetime as dt
import logging
import logging.config
from typing import Union

import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Mediator.abstractMediator import Mediator

logger = logging.getLogger("autotrader")


##############################
### Notification Functions ###
##############################
def send_notification(self, mediator: Mediator, message: str):
    # Build Request
    notification = baseRR.SendNotificationRequestMessage(message)

    # Send notification
    mediator.send_notification(notification)


####################
### DB Functions ###
####################
def get_db_positions(self, mediator: Mediator, strategy_id: int):
    # Build Request
    request = baseRR.ReadOpenPositionsByStrategyIDRequest(strategy_id)

    # Create Order
    return mediator.read_open_db_position_by_strategy_id(request)


def get_db_orders(self, mediator: Mediator, position_id: int):
    # Build Request
    request = baseRR.ReadOrdersByPositionIDRequest(position_id)

    # Create Order
    return mediator.read_orders_by_position_id(request)


def close_db_order(self, mediator: Mediator, order_id: int):
    pass


def close_db_position(self, mediator: Mediator, position_id: int):
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


def get_market_hours(
    mediator: Mediator, date: dt.datetime, strategy_name: str
) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
    # Build Request
    request = baseRR.GetMarketHoursRequestMessage(
        strategy_name, market="OPTION", product="IND", datetime=date
    )

    # Get Market Hours
    return mediator.get_market_hours(request)
