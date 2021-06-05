import abc
from typing import Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR


@attr.s(auto_attribs=True)
class Mediator(abc.ABC):
    killswitch: bool = attr.ib(validator=attr.validators.instance_of(bool))

    @abc.abstractmethod
    def process_strategies(self):
        raise NotImplementedError(
            "Each mediator must implement the 'Process_Strategies' method."
        )

    @abc.abstractmethod
    def get_account(
        self, request: baseRR.GetAccountRequestMessage
    ) -> Union[baseRR.GetAccountResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Get_Account' method."
        )

    @abc.abstractmethod
    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> Union[baseRR.PlaceOrderResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Place_Order' method."
        )

    @abc.abstractmethod
    def cancel_order(
        self, request: baseRR.CancelOrderRequestMessage
    ) -> Union[baseRR.CancelOrderResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Cancel_Order' method."
        )

    @abc.abstractmethod
    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> Union[baseRR.GetOptionChainResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Get_Option_Chain' method."
        )

    @abc.abstractmethod
    def get_market_hours(
        self, request: baseRR.GetMarketHoursRequestMessage
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Get_Market_Hours' method."
        )

    @abc.abstractmethod
    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> Union[baseRR.GetOrderResponseMessage, None]:
        raise NotImplementedError(
            "Each mediator must implement the 'Get_Order' method."
        )

    @abc.abstractmethod
    def send_notification(self, msg: baseRR.SendNotificationRequestMessage) -> None:
        raise NotImplementedError(
            "Each mediator must implement the 'send_notification' method."
        )

    @abc.abstractmethod
    def set_kill_switch(self, kill_switch: baseRR.SetKillSwitchRequestMessage) -> None:
        raise NotImplementedError(
            "Each mediator must implement the 'set_kill_switch' method."
        )
