import abc

import attr

import looptrader.basetypes.Mediator.reqRespTypes as baseRR
from looptrader.basetypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Broker(abc.ABC, Component):
    client_id: str = attr.ib(validator=attr.validators.instance_of(str))
    redirect_uri: str = attr.ib(validator=attr.validators.instance_of(str))
    account_number: str = attr.ib(validator=attr.validators.instance_of(str))
    credentials_path: str = attr.ib(validator=attr.validators.instance_of(str))

    @abc.abstractmethod
    def get_account(
        self, request: baseRR.GetAccountRequestMessage
    ) -> baseRR.GetAccountResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Account' method."
        )

    @abc.abstractmethod
    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> baseRR.PlaceOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Place_Order' method."
        )

    @abc.abstractmethod
    def cancel_order(
        self, request: baseRR.CancelOrderRequestMessage
    ) -> baseRR.CancelOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Cancel_Order' method."
        )

    @abc.abstractmethod
    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> baseRR.GetOptionChainResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Option_Chain' method."
        )

    @abc.abstractmethod
    def get_market_hours(
        self, request: baseRR.GetMarketHoursRequestMessage
    ) -> baseRR.GetMarketHoursResponseMessage:
        """request.markets: The markets for which you're requesting market hours,
        comma-separated. Valid markets are: EQUITY, OPTION, FUTURE, BOND, or FOREX.
        """
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Market_Hours' method."
        )

    @abc.abstractmethod
    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> baseRR.GetOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Order' method."
        )
