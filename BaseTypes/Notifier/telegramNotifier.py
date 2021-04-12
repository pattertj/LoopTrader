import logging
import re
from dataclasses import dataclass, field
from os import getenv

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Mediator.reqRespTypes import GetAccountRequestMessage
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
        dispatcher.add_handler(CommandHandler("account", self.account))
        dispatcher.add_handler(CommandHandler("orders", self.orders))
        dispatcher.add_handler(CommandHandler("positions", self.positions))
        dispatcher.add_handler(CommandHandler("killswitch", self.killswitch))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error)

        # start your shiny new bot
        self.updater.start_polling()

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        self.updater.bot.send_message(chat_id=self.chatid, text=re.escape(request.message), parse_mode='MarkdownV2')

    # function to handle the /start command
    def killswitch(self, update: Update, context: CallbackContext):
        self.mediator.set_kill_switch(True)
        update.message.reply_text('Kill switch, flipped. Awaiting confirmation...')

    # function to handle the /help command
    def help(self, update: Update, context: CallbackContext):
        update.message.reply_text(text=r"Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader\! There are a few things I can do: \r\n\n \- *Push Notifications* will alert you to alerts you setup in your LoopTrader\. \r\n \- */killswitch* will shutdown your LoopTrader\\. \r\n \- */account* will display your latest account details\. \r\n \- */orders* will display your open Orders. \r\n \- */positions* will show your open Positions\\.", parse_mode='MarkdownV2')

    # function to handle /orders command
    def orders(self, update: Update, context: CallbackContext):
        # Get Account
        request = GetAccountRequestMessage(True, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Open Orders: \r\n\n"
        for order in account.orders:
            reply += r"\r\n \- *Order*"

        # Send Message
        try:
            update.message.reply_text(text=reply, parse_mode='MarkdownV2')
        except Exception as e:
            print(e)

    # function to handle /positions command
    def positions(self, update: Update, context: CallbackContext):
        # Get Account
        request = GetAccountRequestMessage(False, True)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Account Positions:"
        for position in account.positions:
            reply += r"\r\n \- *Position*"

        # Send Message
        try:
            update.message.reply_text(text=reply, parse_mode='MarkdownV2')
        except Exception as e:
            print(e)

    # function to handle /account command
    def account(self, update: Update, context: CallbackContext):
        # Get Account
        request = GetAccountRequestMessage(False, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Account Balances:"
        reply += r"\r\n\n \- *Liquidation Value:*" + str(account.currentbalances.liquidationvalue)
        reply += r"\r\n \- *Buying Power:*" + str(account.currentbalances.buyingpower)

        # Send Message
        try:
            update.message.reply_text(text=reply, parse_mode='MarkdownV2')
        except Exception as e:
            print(e)

    # function to handle errors occured in the dispatcher
    def error(self, update: Update, context: CallbackContext):
        update.message.reply_text('An error occured, check the logs.')

    # function to handle normal text
    def text(self, update: Update, context: CallbackContext):
        update.message.reply_text("Sorry, I don't recognize your command.")
