import logging
import logging.config

from basetypes.Broker.tdaBroker import TdaBroker
from basetypes.Database.ormDatabase import ormDatabase
from basetypes.Mediator.botMediator import Bot
from basetypes.Notifier.telegramnotifier import TelegramNotifier
from basetypes.Strategy.longsharesstrategy import LongSharesStrategy
from basetypes.Strategy.singlebydeltastrategy import SingleByDeltaStrategy
from basetypes.Strategy.spreadsbydeltastrategy import SpreadsByDeltaStrategy

if __name__ == "__main__":
    # Create Logging
    logging.config.fileConfig(
        "logConfig.ini",
        defaults={"logfilename": "autotrader.log"},
        disable_existing_loggers=False,
    )

    # Create our strategies
    vgshstrat = LongSharesStrategy(
        strategy_name="VGSH Core", underlying="VGSH", portfolio_allocation_percent=0.9
    )

    cspstrat = SingleByDeltaStrategy(
        strategy_name="Puts",
        put_or_call="PUT",
        target_delta=0.07,
        min_delta=0.03,
        profit_target_percent=(0.95, 0.04, 0.70),
        max_loss_calc_percent=dict({1: 0.2, 2: 0.2}),
    )

    tsla_strat = SingleByDeltaStrategy(
        strategy_name="TSLA Puts",
        put_or_call="PUT",
        underlying="TSLA",
        target_delta=0.05,
        min_delta=0.03,
        minimum_dte=3,
        maximum_dte=7,
        portfolio_allocation_percent=0.05,
        profit_target_percent=0.95,
        max_loss_calc_percent=0.2,
    )

    amzn_strat = SingleByDeltaStrategy(
        strategy_name="AMZN Puts",
        put_or_call="PUT",
        underlying="AMZN",
        target_delta=0.05,
        min_delta=0.03,
        minimum_dte=3,
        maximum_dte=7,
        portfolio_allocation_percent=0.05,
        profit_target_percent=0.95,
        max_loss_calc_percent=0.2,
    )

    nakedcalls = SingleByDeltaStrategy(
        strategy_name="Calls",
        put_or_call="CALL",
        target_delta=0.03,
        min_delta=0.01,
        profit_target_percent=0.83,
        portfolio_allocation_percent=1.5,
        offset_sold_positions=True,
    )

    spreadstrat = SpreadsByDeltaStrategy(strategy_name="spreads", targetdelta=-0.07)

    ira_puts = SingleByDeltaStrategy(
        strategy_name="ira_Puts",
        put_or_call="PUT",
        target_delta=0.07,
        min_delta=0.03,
        profit_target_percent=(0.95, 0.04, 0.70),
        offset_sold_positions=True,
        portfolio_allocation_percent=2.0,
    )

    # Create our brokers
    individualbroker = TdaBroker(id="individual")
    irabroker = TdaBroker(id="ira")

    # Create our local DB
    sqlitedb = ormDatabase("looptrader.db")

    # Create our notifier
    telegram_bot = TelegramNotifier()

    # Create our Bot
    bot = Bot(
        brokerstrategy={
            spreadstrat: irabroker,
            tsla_strat: individualbroker,
            # amzn_strat: individualbroker,
            cspstrat: individualbroker,
            nakedcalls: individualbroker,
            vgshstrat: individualbroker,
        },
        database=sqlitedb,
        notifier=telegram_bot,
    )

    # Run Bot
    bot.process_strategies()
