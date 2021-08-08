import logging
import logging.config

from basetypes.Broker.tdaBroker import TdaBroker
from basetypes.Database.sqliteDatabase import SqliteDatabase
from basetypes.Mediator.botMediator import Bot
from basetypes.Strategy.teststrategy import TestStrategy

if __name__ == "__main__":
    # Create Logging
    logging.config.fileConfig(
        "logConfig.ini",
        defaults={"logfilename": "autotrader.log"},
        disable_existing_loggers=False,
    )

    teststrat = TestStrategy(strategy_name="test")

    # Create our brokers
    individualbroker = TdaBroker(id="individual")
    irabroker = TdaBroker(id="ira")

    # Create our local DB
    sqlitedb = SqliteDatabase("LoopTrader.db")

    # Create our notifier
    telegram_bot = None

    # Create our Bot
    bot = Bot(
        brokerstrategy={
            teststrat: individualbroker,
        },
        database=sqlitedb,
        notifier=telegram_bot,
    )

    # Run Bot
    bot.process_strategies()
