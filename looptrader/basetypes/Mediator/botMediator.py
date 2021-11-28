import logging
import logging.config
import time
from typing import Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Broker.abstractBroker import Broker
from basetypes.Database.abstractDatabase import Database
from basetypes.Mediator.abstractMediator import Mediator
from basetypes.Notifier.abstractnotifier import Notifier
from basetypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True)
class Bot(Mediator):
    notifier: Notifier = attr.ib(validator=attr.validators.instance_of(Notifier))  # type: ignore[misc]
    database: Database = attr.ib(validator=attr.validators.instance_of(Database))  # type: ignore[misc]
    botloopfrequency: int = attr.ib(
        validator=attr.validators.instance_of(int), init=False
    )
    killswitch: bool = attr.ib(
        default=False, validator=attr.validators.instance_of(bool), init=False
    )
    pause: bool = attr.ib(
        default=False, validator=attr.validators.instance_of(bool), init=False
    )
    brokerstrategy: dict[Strategy, Broker] = attr.ib(
        validator=attr.validators.deep_mapping(
            key_validator=attr.validators.instance_of(Strategy),  # type: ignore[misc]
            value_validator=attr.validators.instance_of(Broker),  # type: ignore[misc]
            mapping_validator=attr.validators.instance_of(dict),
        )
    )

    def __attrs_post_init__(self):
        self.botloopfrequency = 60
        self.killswitch = False

        # Set Mediators
        self.database.mediator = self
        self.notifier.mediator = self

        # Validate Broker Strategies and set Mediators
        names = []

        for strategy, broker in self.brokerstrategy.items():
            if strategy.strategy_name in names:
                raise Exception("Duplicate Strategy Name")

            names.append(strategy.strategy_name)
            broker.mediator = self
            strategy.mediator = self

            # Check if Strat exists, create it if needed, store the ID
            result = self.database.read_strategy_by_name(strategy.strategy_name)

            if result == []:
                request = baseRR.CreateDatabaseStrategyRequest(
                    strategy_name=strategy.strategy_name
                )
                strategy.strategy_id = self.database.create_strategy(
                    request
                ).strategy_id
            else:
                strategy.strategy_id = result[0][0]

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
            for strategy in self.brokerstrategy:
                # Check if we are paused
                if not self.pause:
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
    ) -> Union[baseRR.GetAccountResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.get_account(request)

    def get_all_accounts(
        self, request: baseRR.GetAllAccountsRequestMessage
    ) -> Union[baseRR.GetAllAccountsResponseMessage, None]:

        response = baseRR.GetAllAccountsResponseMessage()
        response.accounts = []

        distinct_brokers = list(set(self.brokerstrategy.keys()))

        for strategy in distinct_brokers:
            broker = self.get_broker(strategy.strategy_name)

            if broker is None:
                continue

            acct_request = baseRR.GetAccountRequestMessage(
                strategy.strategy_name, request.orders, request.positions
            )

            account = broker.get_account(acct_request)

            if account is not None:
                response.accounts.append(account)

        return response

    def place_order(
        self, request: baseRR.PlaceOrderRequestMessage
    ) -> Union[baseRR.PlaceOrderResponseMessage, None]:
        broker = self.get_broker(request.order.strategy)

        if broker is None:
            return None

        return broker.place_order(request)

    def cancel_order(
        self, request: baseRR.CancelOrderRequestMessage
    ) -> Union[baseRR.CancelOrderResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.cancel_order(request)

    def get_order(
        self, request: baseRR.GetOrderRequestMessage
    ) -> Union[baseRR.GetOrderResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.get_order(request)

    def get_market_hours(
        self, request: baseRR.GetMarketHoursRequestMessage
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.get_market_hours(request)

    def get_quote(
        self, request: baseRR.GetQuoteRequestMessage
    ) -> Union[baseRR.GetQuoteResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.get_quote(request)

    def get_option_chain(
        self, request: baseRR.GetOptionChainRequestMessage
    ) -> Union[baseRR.GetOptionChainResponseMessage, None]:
        broker = self.get_broker(request.strategy_name)

        if broker is None:
            return None

        return broker.get_option_chain(request)

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        self.notifier.send_notification(request)

    def set_kill_switch(self, request: baseRR.SetKillSwitchRequestMessage) -> None:
        self.killswitch = request.kill_switch

    def pause_bot(self) -> None:
        self.pause = True

    def resume_bot(self) -> None:
        self.pause = False

    def get_broker(self, strategy_name: str) -> Union[Broker, None]:
        """Returns the broker object associated to a given strategy

        Args:
            strategy_name (str): Name of the Strategy to search

        Returns:
            Broker: Associated Broker object
        """
        for strategy, broker in self.brokerstrategy.items():
            if strategy.strategy_name == strategy_name:
                return broker

        return None

    def get_all_strategies(self) -> list[str]:
        strategies = list[str]()

        for strategy in self.brokerstrategy.keys():
            strategies.append(strategy.strategy_name)

        return strategies

    # TODO: Fix Strategy
    # def create_db_strategy(
    #     self, request: baseRR.CreateDatabaseStrategyRequest
    # ) -> Union[baseRR.CreateDatabaseStrategyResponse, None]:
    #     return self.database.create_strategy(request)

    def create_db_order(
        self, request: baseRR.CreateDatabaseOrderRequest
    ) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        return self.database.create_order(request)
