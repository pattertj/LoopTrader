import logging
import logging.config

from BaseTypes.Broker.tdaBroker import TdaBroker
from BaseTypes.Database.sqliteDatabase import SqliteDatabase
from BaseTypes.Mediator.botMediator import Bot
from BaseTypes.Notifier.telegramNotifier import TelegramNotifier
from BaseTypes.Strategy.cspStrategy import CspStrategy

# Create Logging
logging.config.fileConfig("logConfig.ini", defaults={
                          'logfilename': 'autotrader.log'}, disable_existing_loggers=False)

# Create our strategies
cspstrat = CspStrategy(strategy_name="CSP1")
cspstrat1 = CspStrategy(strategy_name="CSP2")
cspstrat2 = CspStrategy(strategy_name="CSP3")

# Create our broker
tdabroker = TdaBroker()

# Create our local DB
sqlitedb = SqliteDatabase()

# Create our notifier
telegram_bot = TelegramNotifier()

# Create our Bot
bot = Bot(broker=tdabroker, strategies=[cspstrat, cspstrat1, cspstrat2], database=sqlitedb)

# Run Bot
bot.process_strategies()
