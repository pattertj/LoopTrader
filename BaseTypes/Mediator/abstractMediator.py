import abc

import attr
import basetypes.Mediator.reqRespTypes as baseRR


@attr.s(auto_attribs=True)
class Mediator(abc.ABC):
    killswitch: bool = attr.ib(validator=attr.validators.instance_of(bool))

    @abc.abstractmethod
    def process_strategies(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'Process_Strategies' method.")

    @abc.abstractmethod
    def get_account(self, request: baseRR.GetAccountRequestMessage) -> baseRR.GetAccountResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Account' method.")

    @abc.abstractmethod
    def place_order(self, request: baseRR.PlaceOrderRequestMessage) -> baseRR.PlaceOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Place_Order' method.")

    @abc.abstractmethod
    def cancel_order(self, request: baseRR.CancelOrderRequestMessage) -> baseRR.CancelOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Cancel_Order' method.")

    @abc.abstractmethod
    def get_option_chain(self, request: baseRR.GetOptionChainRequestMessage) -> baseRR.GetOptionChainResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Option_Chain' method.")

    @abc.abstractmethod
    def get_market_hours(self, request: baseRR.GetMarketHoursRequestMessage) -> baseRR.GetMarketHoursResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Market_Hours' method.")

    @abc.abstractmethod
    def get_order(self, request: baseRR.GetOrderRequestMessage) -> baseRR.GetOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Order' method.")

    @abc.abstractmethod
    def send_notification(self, msg: str) -> None:
        raise NotImplementedError(
            "Each strategy must implement the 'send_notification' method.")

    @abc.abstractmethod
    def set_kill_switch(self, kill_switch: bool) -> None:
        raise NotImplementedError(
            "Each strategy must implement the 'set_kill_switch' method.")
