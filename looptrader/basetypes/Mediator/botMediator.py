import logging
import logging.config
import time

import attr
import basetypes.Mediator.reqRespTypes as baseRR

from looptrader.basetypes.Broker.abstractBroker import Broker
from looptrader.basetypes.Database.abstractDatabase import Database
from looptrader.basetypes.Mediator.abstractMediator import Mediator
from looptrader.basetypes.Notifier.abstractnotifier import Notifier
from looptrader.basetypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True)
class Bot(Mediator):
    broker: Broker = attr.ib(validator=attr.validators.instance_of(Broker))
    notifier: Notifier = attr.ib(validator=attr.validators.instance_of(Notifier))
    database: Database = attr.ib(validator=attr.validators.instance_of(Database))
    botloopfrequency: int = attr.ib(
        validator=attr.validators.instance_of(int), init=False
    )
    killswitch: bool = attr.ib(
        default=False, validator=attr.validators.instance_of(bool), init=False
    )
    strategies: list[Strategy] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(Strategy),
            iterable_validator=attr.validators.instance_of(list),
        )
    )

    def __attrs_post_init__(self):
        self.botloopfrequency = 30
        self.killswitch = False

        # Validate Strategies
        names = []
        for strategy in self.strategies:
            if strategy.strategy_name in names:
                raise Exception("Duplicate Strategy Name")
            else:
                names.append(strategy.strategy_name)

        # Set Mediators
        self.database.mediator = self
        self.broker.mediator = self
        self.notifier.mediator = self
        for strategy in self.strategies:
            # strat = re.findall(r"(\w+(?=\'))", str(type(strategy)))
            # name = strategy.strategy_name
            # under = strategy.underlying
            strategy.mediator = self

    def process_strategies(self):
        # Get the current timestamp
        starttime = time.time()

        # If the loop is exited, send a notification
        self.send_notification(
            baseRR.SendNotificationRequestMessage(message="Bot Started.")
        )

        # While the kill switch is not enabled, loop through strategies
        while not self.killswitch:

            # Process each strategy sequentially
            strategy: Strategy
            for strategy in self.strategies:
                strategy.process_strategy()

            # Sleep for the specified time.
            logger.info("Sleeping...")
            time.sleep(
                self.botloopfrequency
                - ((time.time() - starttime) % self.botloopfrequency)
            )

        # If the loop is exited, send a notification
        self.send_notification(
            baseRR.SendNotificationRequestMessage(message="Bot Terminated.")
        )

    def get_account(
        self, request: baseRR.GetAccountRequestMessage
    ) -> baseRR.GetAccountResponseMessage:
        return self.broker.get_account(request)

    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> baseRR.PlaceOrderResponseMessage:
        return self.broker.place_order(request)

    def cancel_order(
        self, request: baseRR.CancelOrderRequestMessage
    ) -> baseRR.CancelOrderResponseMessage:
        return self.broker.cancel_order(request)

    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> baseRR.GetOrderResponseMessage:
        return self.broker.get_order(request)

    def get_market_hours(
        self, request: baseRR.GetMarketHoursRequestMessage
    ) -> baseRR.GetMarketHoursResponseMessage:
        return self.broker.get_market_hours(request)

    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> baseRR.GetOptionChainResponseMessage:
        return self.broker.get_option_chain(request)

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        self.notifier.send_notification(request)

    def set_kill_switch(self, request: baseRR.SetKillSwitchRequestMessage) -> None:
        self.killswitch = request.kill_switch
