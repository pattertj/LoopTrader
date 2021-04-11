import logging
import logging.config
import time
from dataclasses import dataclass, field

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Broker.abstractBroker import Broker
from BaseTypes.Database.abstractDatabase import Database
from BaseTypes.Mediator.abstractMediator import Mediator
from BaseTypes.Notifier.abstractNotifier import Notifier
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@dataclass
class Bot(Mediator):
    broker: Broker
    notifier: Notifier
    database: Database
    botloopfrequency: int = field(init=False)
    killswitch: bool = field(init=False)
    strategies: list[Strategy] = field(default_factory=list)

    def __post_init__(self):
        self.botloopfrequency = 30
        self.killswitch = False

        # Set Mediators
        self.database.mediator = self
        self.broker.mediator = self
        self.notifier.mediator = self
        for strategy in self.strategies:
            strategy.mediator = self

    def process_strategies(self) -> bool:
        # Get the current timestamp
        starttime = time.time()

        # While the kill switch is not enabled, loop through strategies
        while not self.killswitch:

            # Process each strategy sequentially
            for strategy in self.strategies:
                strategy.processstrategy()

            # Sleep for the specified time.
            time.sleep(self.botloopfrequency - ((time.time() - starttime) % self.botloopfrequency))

        # If the loop is exited, send a notification
        self.send_notification("Bot Terminated.")

    def get_account(self, request: baseRR.GetAccountRequestMessage) -> baseRR.GetAccountResponseMessage:
        return self.broker.get_account(request)

    def place_order(self, request: baseRR.PlaceOrderRequestMessage) -> baseRR.PlaceOrderResponseMessage:
        return self.broker.place_order(request)

    def cancel_order(self, request: baseRR.CancelOrderRequestMessage) -> baseRR.CancelOrderResponseMessage:
        return self.broker.cancel_order(request)

    def get_order(self, request: baseRR.GetOrderRequestMessage) -> baseRR.GetOrderResponseMessage:
        return self.broker.get_order(request)

    def get_market_hours(self, request: baseRR.GetMarketHoursRequestMessage) -> baseRR.GetMarketHoursResponseMessage:
        return self.broker.get_market_hours(request)

    def get_option_chain(self, request: baseRR.GetOptionChainRequestMessage) -> baseRR.GetOptionChainResponseMessage:
        return self.broker.get_option_chain(request)

    def send_notification(self, msg: str) -> None:
        self.notifier.send_notification(msg)

    def set_kill_switch(self, kill_switch: bool) -> None:
        self.killswitch = kill_switch
