import logging
from dataclasses import dataclass
from os import getenv

# import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Notifier.abstractNotifier import Notifier
from BaseTypes.Component.abstractComponent import Component
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logger = logging.getLogger('autotrader')


@dataclass
class TelegramNotifier(Notifier, Component):
    token: str = getenv('TELEGRAM_TOKEN')

    def __post_init__(self):
        # create the updater, that will automatically create also a dispatcher and a queue to make them dialoge
        updater = Updater(self.token, use_context=True)
        dispatcher = updater.dispatcher

        # add handlers for start and help commands
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", help))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error)

        # start your shiny new bot
        updater.start_polling()

    def do_something(self) -> None:
        pass

    # function to handle the /start command
    def start(self, update, context):
        update.message.reply_text('start command received')

    # function to handle the /help command
    def help(self, update, context):
        update.message.reply_text('help command received')

    # function to handle errors occured in the dispatcher
    def error(self, update, context):
        update.message.reply_text('an error occured')

    # function to handle normal text
    def text(self, update, context):
        update.message.reply_text("Hi Monia")
        # text_received = update.message.text
        # update.message.reply_text(f'did you said "{text_received}" ?')
