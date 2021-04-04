import logging
import logging.config
import time
from dataclasses import dataclass, field

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Broker.abstractBroker import Broker
from BaseTypes.Database.abstractDatabase import Database
from BaseTypes.Mediator.abstractMediator import Mediator
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@dataclass
class Bot(Mediator):
    broker: Broker
    database: Database
    strategies: list[Strategy] = field(default_factory=list)
    botloopfrequency: int = 30

    def __post_init__(self):
        self.database.mediator = self
        self.broker.mediator = self
        for strategy in self.strategies:
            strategy.mediator = self

    def process_strategies(self) -> bool:
        starttime = time.time()

        while True:

            for strategy in self.strategies:
                strategy.processstrategy()

            time.sleep(self.botloopfrequency - ((time.time() - starttime) % self.botloopfrequency))

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
