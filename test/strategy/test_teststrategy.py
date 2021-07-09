# # import os
# import os

# from basetypes.Broker.tdaBroker import TdaBroker
# from basetypes.Database.sqliteDatabase import SqliteDatabase
# from basetypes.Mediator.botMediator import Bot
# from basetypes.Notifier.telegramnotifier import TelegramNotifier
# from basetypes.Strategy.teststrategy import TestStrategy


# def test_process_core_open_market():
#     """This test will always pass. It's primarily how I debug the strategies off-hours. The test function can be changed, but this is the pattern. I leave it commented out when not in use since it is not a real test."""
#     # Create our strategy
#     teststrat = TestStrategy(strategy_name="test")

#     # Create our broker
#     testbroker = TdaBroker(id="individual")

#     # Create our local DB
#     sqlitedb = SqliteDatabase("looptrader.db")

#     # Create our notifier
#     telegram_bot = TelegramNotifier()

#     # Create our Bot
#     bot = Bot(
#         brokerstrategy={teststrat: testbroker},
#         database=sqlitedb,
#         notifier=telegram_bot,
#     )

#     # Assign bot to the strat
#     teststrat.mediator = bot

#     # Test our function
#     result = teststrat.process_core_open_market()

#     os.remove("testdb.db")

#     # Check results
#     assert result is None or result is not None
