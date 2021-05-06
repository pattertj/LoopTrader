from BaseTypes.Strategy.staggeredStrangleStrategy import StaggeredStrangleStrategy
import logging
import logging.config

from BaseTypes.Broker.tdaBroker import TdaBroker
from BaseTypes.Database.sqliteDatabase import SqliteDatabase
from BaseTypes.Mediator.botMediator import Bot
from BaseTypes.Notifier.telegramNotifier import TelegramNotifier
from BaseTypes.Strategy.cspByDeltaStrategy import CspByDeltaStrategy

# Create Logging
logging.config.fileConfig("logConfig.ini", defaults={
                          'logfilename': 'autotrader.log'}, disable_existing_loggers=False)

# Create our strategies
cspstrat = StaggeredStrangleStrategy(strategy_name="SSS")

# Create our broker
tdabroker = TdaBroker()

# Create our local DB
sqlitedb = SqliteDatabase("LoopTrader.db")

# Create our notifier
telegram_bot = TelegramNotifier()

# Create our Bot
bot = Bot(broker=tdabroker, strategies=[cspstrat], database=sqlitedb, notifier=telegram_bot)

# Run Bot
bot.process_strategies()
