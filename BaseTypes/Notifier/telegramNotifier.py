import logging
import re
from os import getenv

import attr
from telegram.callbackquery import CallbackQuery
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Mediator.reqRespTypes import GetAccountRequestMessage
from BaseTypes.Notifier.abstractNotifier import Notifier
from telegram import ParseMode, Update
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram.ext.callbackcontext import CallbackContext
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

logger = logging.getLogger('autotrader')


@attr.s(auto_attribs=True)
class TelegramNotifier(Notifier, Component):
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
        dispatcher.add_handler(CommandHandler("positions", self.positions))
        dispatcher.add_handler(CommandHandler("killswitch", self.killswitch))
        dispatcher.add_handler(CallbackQueryHandler(self.button))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error)

        # start your shiny new bot
        self.updater.start_polling()

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        self.send_message(text=re.escape(request.message), parsemode=ParseMode.MARKDOWN_V2)

    # function to handle the /start command
    def start(self, update: Update, context: CallbackContext):
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
            self.reply_text(text, update, reply_markup, ParseMode.MARKDOWN_V2)
        except Exception as e:
            print(e)

    # function to handle the /killswitch command
    def killswitch(self, update: Update, context: CallbackContext):
        self.mediator.set_kill_switch(True)
        self.reply_text(r"Kill switch, flipped. Awaiting confirmation...", update, None, ParseMode.MARKDOWN_V2)

    # function to handle the /help command
    def help(self, update: Update, context: CallbackContext):
        self.reply_text(r"Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader\! There are a few things I can do: \r\n\n \- *Push Notifications* will alert you to alerts you setup in your LoopTrader\. \r\n \- */killswitch* will shutdown your LoopTrader\\. \r\n \- */account* will display your latest account details\. \r\n \- */orders* will display your open Orders. \r\n \- */positions* will show your open Positions\\.", update, None, ParseMode.MARKDOWN_V2)

    # function to handle /orders command
    def orders(self, update: Update, context: CallbackContext):
        # Build Message
        msg = self.build_orders_message()

        # Send Message
        self.reply_text(msg, update, None, ParseMode.HTML)

    # function to handle /positions command
    def positions(self, update: Update, context: CallbackContext):
        # Build Message
        msg = self.build_positions_message()

        # Send Message
        self.reply_text(msg, update, None, ParseMode.HTML)

    # function to handle /account command
    def balances(self, update: Update, context: CallbackContext):
        # Build Message
        msg = self.build_balances_message()

        # Send Message
        self.reply_text(msg, update, None, ParseMode.HTML)

    # function to handle errors occured in the dispatcher
    def error(self, update: Update, context: CallbackContext):
        self.reply_text(r"An error occured, check the logs.", update, None, ParseMode.HTML)

    # function to handle normal text
    def text(self, update: Update, context: CallbackContext):
        self.reply_text(r"Sorry, I don't recognize your command.", update, None, ParseMode.HTML)

    def build_balances_message(self) -> str:
        # Get Account
        request = GetAccountRequestMessage(False, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Account Balances:"
        reply += "\r\n - <b>Liquidation Value:</b> <code>${}</code>".format("{:,.2f}".format(account.currentbalances.liquidationvalue))
        reply += "\r\n - <b>Buying Power:</b> <code>${}</code>".format("{:,.2f}".format(account.currentbalances.buyingpower))

        return reply

    def build_positions_message(self) -> str:
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
        # Get Account
        request = GetAccountRequestMessage(True, False)
        account = self.mediator.get_account(request)

        # Build Reply
        reply = r"Open Orders:"

        for order in account.orders:
            if order.status == 'OPEN' or order.status == 'QUEUED':
                reply += " \r\n <code>- {}x {} {} @ ${}</code>".format(str(order.quantity), str(order.legs[0].instruction), str(order.legs[0].symbol), "{:,.2f}".format(order.price))

        return reply

    def button(self, update: Update, _: CallbackContext) -> None:
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
        except Exception as e:
            print(e)

    # Send Message/Reply Helpers
    def send_message(self, message: str, parsemode: ParseMode):
        try:
            self.updater.bot.send_message(chat_id=self.chatid, text=message, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to send message.")
            pass

    def reply_text(self, text: str, update: Update, reply_markup: InlineKeyboardMarkup, parsemode: ParseMode):
        try:
            update.message.reply_text(text, reply_markup=reply_markup, quote=False, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to reply.")
            pass

    def edit_message_text(self, query: CallbackQuery, msg: str, parsemode: ParseMode):
        try:
            query.edit_message_text(text=msg, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to callback.")
            pass
