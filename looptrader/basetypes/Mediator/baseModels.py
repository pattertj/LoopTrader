from typing import Optional
import attr
from datetime import datetime


class ExecutionLeg:
    id: Optional[int] = attr.ib(default=None)
    leg_id: int = attr.ib(validator=attr.validators.instance_of(int))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    mismarked_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    time: datetime = attr.ib(validator=attr.validators.instance_of(datetime))

class OrderActivity:
    id: Optional[int] = attr.ib(default=None)
    activity_type: str = attr.ib(validator=attr.validators.instance_of(str))
    execution_type: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    order_remaining_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    execution_legs: list[ExecutionLeg] = attr.ib(validator=attr.validators.instance_of(list[ExecutionLeg]))
    
class OrderLeg:
    id: Optional[int] = attr.ib(default=None)
    asset_type: str = attr.ib(validator=attr.validators.instance_of(str))
    cusip: str = attr.ib(validator=attr.validators.instance_of(str))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    instruction: str = attr.ib(validator=attr.validators.instance_of(str))
    position_effect: str = attr.ib(validator=attr.validators.instance_of(str))
    put_call: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    leg_id: int = attr.ib(validator=attr.validators.instance_of(int))
    
# class Strategy:
#     id: Optional[int] = attr.ib(default=None)
#     name: str = attr.ib(validator=attr.validators.instance_of(str))

class Order:
    id: Optional[int] = attr.ib(default=None)
    session: str = attr.ib(validator=attr.validators.instance_of(str))
    duration: str = attr.ib(validator=attr.validators.instance_of(str))
    order_type: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    filled_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    remaining_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    requested_destination: str = attr.ib(validator=attr.validators.instance_of(str))
    destination_link_name: str = attr.ib(validator=attr.validators.instance_of(str))
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    order_strategy_type: str = attr.ib(validator=attr.validators.instance_of(str))
    cancelable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    editable: bool = attr.ib(validator=attr.validators.instance_of(bool))
    status: str = attr.ib(validator=attr.validators.instance_of(str))
    entered_time: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    close_time: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    account_id: int = attr.ib(validator=attr.validators.instance_of(int))
    order_id: int = attr.ib(validator=attr.validators.instance_of(int))
    legs: list[OrderLeg] = attr.ib(validator=attr.validators.instance_of(list[OrderLeg]))
    activities: list[OrderActivity] = attr.ib(validator=attr.validators.instance_of(list[OrderActivity]))
    strategy: str = attr.ib(validator=attr.validators.instance_of(str))