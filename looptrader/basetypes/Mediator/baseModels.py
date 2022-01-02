from datetime import date, datetime
from typing import Optional

import attr


@attr.s(auto_attribs=True, init=False)
class ExecutionLeg:
    id: Optional[int] = attr.ib(
        default=None, init=False, validator=attr.validators.instance_of(int)
    )
    leg_id: int = attr.ib(validator=attr.validators.instance_of(int))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    mismarked_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    price: float = attr.ib(validator=attr.validators.instance_of(float))
    time: datetime = attr.ib(validator=attr.validators.instance_of(datetime))
    orderactivity_id: int = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(auto_attribs=True, init=False)
class OrderActivity:
    id: Optional[int] = attr.ib(
        default=None, init=False, validator=attr.validators.instance_of(int)
    )
    activity_type: str = attr.ib(validator=attr.validators.instance_of(str))
    execution_type: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    order_remaining_quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    order_id: int = attr.ib(validator=attr.validators.instance_of(int))
    execution_legs: list[ExecutionLeg] = attr.ib(
        validator=attr.validators.instance_of(list[ExecutionLeg])
    )


@attr.s(auto_attribs=True, init=False)
class OrderLeg:
    id: Optional[int] = attr.ib(
        default=None, init=False, validator=attr.validators.instance_of(int)
    )
    asset_type: str = attr.ib(validator=attr.validators.instance_of(str))
    cusip: str = attr.ib(validator=attr.validators.instance_of(str))
    symbol: str = attr.ib(validator=attr.validators.instance_of(str))
    description: str = attr.ib(validator=attr.validators.instance_of(str))
    instruction: str = attr.ib(validator=attr.validators.instance_of(str))
    position_effect: str = attr.ib(validator=attr.validators.instance_of(str))
    put_call: str = attr.ib(validator=attr.validators.instance_of(str))
    quantity: int = attr.ib(validator=attr.validators.instance_of(int))
    leg_id: int = attr.ib(validator=attr.validators.instance_of(int))
    order_id: int = attr.ib(validator=attr.validators.instance_of(int))
    expiration_date: date = attr.ib(validator=attr.validators.instance_of(date))


@attr.s(auto_attribs=True, init=False)
class Strategy:
    id: Optional[int] = attr.ib(
        default=None, init=False, validator=attr.validators.instance_of(int)
    )
    name: str = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(auto_attribs=True, init=False)
class Order:
    id: Optional[int] = attr.ib(
        default=None, init=False, validator=attr.validators.instance_of(int)
    )
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
    strategy_id: int = attr.ib(validator=attr.validators.instance_of(int))
    legs: list[OrderLeg] = attr.ib(
        validator=attr.validators.instance_of(list[OrderLeg])
    )
    activities: list[OrderActivity] = attr.ib(
        validator=attr.validators.instance_of(list[OrderActivity])
    )

    def isActive(self):
        return self.status not in [
            "REJECTED",
            "CANCELED",
            "FILLED",
            "EXPIRED",
            "REPLACED",
        ]
