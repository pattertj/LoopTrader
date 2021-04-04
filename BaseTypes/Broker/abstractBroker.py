from BaseTypes.Component.abstractComponent import Component
import abc
from dataclasses import dataclass

import BaseTypes.Mediator.reqRespTypes as baseRR


@dataclass
class Broker(abc.ABC, Component):
    client_id: str
    redirect_uri: str
    account_number: str
    credentials_path: str

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
        ''' request.markets: The markets for which you're requesting market hours,
        comma-separated. Valid markets are: EQUITY, OPTION, FUTURE, BOND, or FOREX.
        '''
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Market_Hours' method.")

    @abc.abstractmethod
    def get_order(self, request: baseRR.GetOrderRequestMessage) -> baseRR.GetOrderResponseMessage:
        raise NotImplementedError(
            "Each strategy must implement the 'Get_Order' method.")
