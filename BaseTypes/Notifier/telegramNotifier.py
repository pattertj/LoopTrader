import logging
import re
from dataclasses import dataclass, field
from os import getenv

from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Notifier.abstractNotifier import Notifier
from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram.ext.callbackcontext import CallbackContext

logger = logging.getLogger('autotrader')


@dataclass
class TelegramNotifier(Notifier, Component):
    updater: Updater = field(init=False)
    chatid: int = field(init=False)

    def __post_init__(self):
        token = getenv('TELEGRAM_TOKEN')
        self.chatid = getenv('TELEGRAM_CHATID')

        # create the updater, that will automatically create also a dispatcher and a queue to make them dialoge
        self.updater = Updater(token, use_context=True)
        dispatcher = self.updater.dispatcher

        # add handlers for start and help commands
        #  dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("killswitch", self.killswitch))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error)

        # start your shiny new bot
        self.updater.start_polling()

    def send_notification(self, msg: str) -> None:
        self.updater.bot.send_message(chat_id=self.chatid, text=re.escape(msg), parse_mode='MarkdownV2')

    # function to handle the /start command
    def killswitch(self, update: Update, context: CallbackContext):
        self.mediator.set_kill_switch(True)
        update.message.reply_text('Kill Switch, Flipped')

    # function to handle the /help command
    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text('help command received')

    # function to handle errors occured in the dispatcher
    def error(self, update: Update, context: CallbackContext):
        update.message.reply_text('an error occured')

    # function to handle normal text
    def text(self, update: Update, context: CallbackContext):
        text_received = update.message.text
        update.message.reply_text(f'did you said "{text_received}" ?')
