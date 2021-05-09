'''
The concrete implementation of the generic LoopTrader Notifier class for communication with Telegram.

Classes:

    TelegramNotifier

Functions:

    send_notification(request: baseRR.SendNotificationRequestMessage) -> None
'''
import logging
import re
from os import getenv

import attr
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Mediator.reqRespTypes import GetAccountRequestMessage
from BaseTypes.Notifier.abstractnotifier import Notifier
from telegram import ParseMode, Update
from telegram.callbackquery import CallbackQuery
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram.ext.callbackcontext import CallbackContext
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.message import Message

logger = logging.getLogger('autotrader')


@attr.s(auto_attribs=True)
class TelegramNotifier(Notifier, Component):
    '''The concrete implementation of the generic LoopTrader Notifier class for communication with Telegram.'''

    updater: Updater = attr.ib(validator=attr.validators.instance_of(Updater), init=False)
    chatid: int = attr.ib(validator=attr.validators.instance_of(int), init=False)

    def __attrs_post_init__(self):
        token = getenv('TELEGRAM_TOKEN')
        self.chatid = int(getenv('TELEGRAM_CHATID'))

        # create the updater, that will automatically create also a dispatcher and a queue to make them dialoge
        self.updater = Updater(token, use_context=True)
        dispatcher = self.updater.dispatcher

        # add handlers for start and help commands
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("balances", self.balances))
        dispatcher.add_handler(CommandHandler("orders", self.orders))
        dispatcher.add_handler(CommandHandler("tail", self.tail, pass_args=True))
        dispatcher.add_handler(CommandHandler("positions", self.positions))
        dispatcher.add_handler(CommandHandler("killswitch", self.killswitch))
        dispatcher.add_handler(CallbackQueryHandler(self.button))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error, False)

        # start your shiny new bot
        self.updater.start_polling()

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        self.send_message(message=re.escape(request.message), parsemode=ParseMode.MARKDOWN_V2)

    def start(self, update: Update, context: CallbackContext):
        '''Method to handle the /start command'''
        keyboard = [
            [
                InlineKeyboardButton("Balances", callback_data='1'),
                InlineKeyboardButton("Positions", callback_data='2'),
                InlineKeyboardButton("Orders", callback_data='3')
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            text = r"Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader\! There are a few things I can do:"
            self.reply_text(text, update.message, reply_markup, ParseMode.MARKDOWN_V2)
        except Exception:
            logger.exception("Failed to reply to /start command.")

    def killswitch(self, update: Update, context: CallbackContext):
        '''Method to handle the /killswitch command'''
        self.mediator.set_kill_switch(True)
        self.reply_text(r"Kill switch, flipped. Awaiting confirmation...", update.message, None, ParseMode.MARKDOWN_V2)

    def help(self, update: Update, context: CallbackContext):
        '''Method to handle the /help command'''
        self.reply_text(r"Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader\! There are a few things I can do: \r\n\n \- *Push Notifications* will alert you to alerts you setup in your LoopTrader\. \r\n \- */killswitch* will shutdown your LoopTrader\\. \r\n \- */account* will display your latest account details\. \r\n \- */orders* will display your open Orders. \r\n \- */positions* will show your open Positions\\.", update.message, None, ParseMode.MARKDOWN_V2)

    def orders(self, update: Update, context: CallbackContext):
        '''Method to handle the /orders command'''
        # Build Message
        msg = self.build_orders_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def positions(self, update: Update, context: CallbackContext):
        '''Method to handle the /positions command'''
        # Build Message
        msg = self.build_positions_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def tail(self, update: Update, context: CallbackContext):
        '''Method to handle the /tail command'''
        # Make sure only one arg was sent
        if len(context.args) != 1:
            self.reply_text("There was an error with your input. Please enter a single integer.", update.message, None, ParseMode.HTML)
            return

        # Try to read the arg
        try:
            rows = int(context.args[0])
        except Exception:
            self.reply_text("There was an error with your input. Please enter an integer.", update.message, None, ParseMode.HTML)
            return

        # Validate the provided integer
        if rows <= 0:
            self.reply_text("There was an error with your input. Please enter a positive integer.", update.message, None, ParseMode.HTML)
            return

        # Build reply
        reply = "Log Tail:"

        # Open the log using with() method so that the file gets closed after completing the work
        with open("autotrader.log") as file:
            # Loop to read iterate last X rows
            for line in file.readlines()[-rows:]:
                reply += "\r\n {}".format(line)

        # Send Message
        self.reply_text(reply, update.message, None, ParseMode.HTML)

    def balances(self, update: Update, context: CallbackContext):
        '''Method to handle the /balances command'''
        # Build Message
        msg = self.build_balances_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def error(self, update: Update, context: CallbackContext):
        '''Method to handle errors occurring in the dispatcher'''
        self.reply_text(r"An error occured, check the logs.", update.message, None, ParseMode.HTML)

    def text(self, update: Update, context: CallbackContext):
        '''Method to handle normal text'''
        self.reply_text(r"Sorry, I don't recognize your command.", update.message, None, ParseMode.HTML)

    def button(self, update: Update, _: CallbackContext) -> None:
        '''Method to handle /start command inline keyboard clicks '''
        query = update.callback_query

        query.answer()

        if query.data == '1':
            msg = self.build_balances_message()
        elif query.data == '2':
            msg = self.build_positions_message()
        elif query.data == '3':
            msg = self.build_orders_message()

        try:
            self.edit_message_text(query, msg, ParseMode.HTML)
        except Exception:
            logger.exception("Telegram failed to callback.")

    # Helper Methods
    def build_balances_message(self) -> str:
        '''Method to build the message string for the /balances command'''
        # Get Account
        request = GetAccountRequestMessage(False, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Account Balances:"
        reply += "\r\n - <b>Liquidation Value:</b> <code>${}</code>".format("{:,.2f}".format(account.currentbalances.liquidationvalue))
        reply += "\r\n - <b>Buying Power:</b> <code>${}</code>".format("{:,.2f}".format(account.currentbalances.buyingpower))

        return reply

    def build_positions_message(self) -> str:
        '''Method to build the message string for the /positions command'''
        # Get Account
        request = GetAccountRequestMessage(False, True)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Account Positions:"

        for position in account.positions:
            qty = position.shortquantity + position.longquantity
            reply += " \r\n <code>- {}x {} @ ${}</code>".format(str(qty), str(position.symbol), "{:,.2f}".format(position.averageprice))

        return reply

    def build_orders_message(self) -> str:
        '''Method to build the message string for the /orders command'''
        # Get Account
        request = GetAccountRequestMessage(True, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Open Orders:"

        for order in account.orders:
            if order.status in ['OPEN', 'QUEUED']:
                price = 0 if order.price is None else order.price
                reply += " \r\n <code>- {}x {} {} @ ${}</code>".format(str(order.quantity), str(order.legs[0].instruction), str(order.legs[0].symbol), "{:,.2f}".format(price))

        return reply

    def send_message(self, message: str, parsemode: ParseMode):
        '''Wrapper method to send messages to a user'''
        try:
            bot = self.updater.bot
            bot.send_message(chat_id=self.chatid, text=message, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to send message.")

    @staticmethod
    def reply_text(text: str, message: Message, reply_markup: InlineKeyboardMarkup, parsemode: ParseMode):
        '''Wrapper method to send reply texts'''
        try:
            message.reply_text(text, reply_markup=reply_markup, quote=False, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to reply.")

    @staticmethod
    def edit_message_text(query: CallbackQuery, msg: str, parsemode: ParseMode):
        '''Wrapper method to edit message texts'''
        try:
            query.edit_message_text(text=msg, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to callback.")
