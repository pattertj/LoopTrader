"""
The concrete implementation of the generic LoopTrader Notifier class for communication with Telegram.

Classes:

    TelegramNotifier

Functions:

    send_notification(request: baseRR.SendNotificationRequestMessage) -> None
"""
import logging
from os import getenv
from typing import Optional, Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Component.abstractComponent import Component
from basetypes.Mediator.reqRespTypes import GetAllAccountsRequestMessage
from basetypes.Notifier.abstractnotifier import Notifier
from dotenv import load_dotenv
from telegram import ParseMode, Update
from telegram.callbackquery import CallbackQuery
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.dispatcher import Dispatcher
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.message import Message
from telegram.utils.helpers import DefaultValue

logger = logging.getLogger("autotrader")
load_dotenv()


@attr.s(auto_attribs=True)
class TelegramNotifier(Notifier, Component):
    """The concrete implementation of the generic LoopTrader Notifier class for communication with Telegram."""

    updater: Updater = attr.ib(
        validator=attr.validators.instance_of(Updater), init=False
    )
    chatid: int = attr.ib(validator=attr.validators.instance_of(int), init=False)

    def __attrs_post_init__(self):
        token = getenv("TELEGRAM_TOKEN")
        self.chatid = int(getenv("TELEGRAM_CHATID"))

        # Create the updater, that will automatically create also a dispatcher and a queue to make them dialoge
        self.updater = Updater(token, use_context=True)
        dispatcher = self.updater.dispatcher

        # Add handlers for start and help commands
        self.add_handlers(dispatcher)

        # Start your shiny new bot
        self.updater.start_polling()

    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        """Method to handle bot requests to push notifications"""
        self.send_message(message=request.message, parsemode=request.parsemode)

    def start(self, update: Update, context: CallbackContext):
        """Method to handle the /start command"""
        keyboard = [
            [
                InlineKeyboardButton("Balances", callback_data="1"),
                InlineKeyboardButton("Positions", callback_data="2"),
                InlineKeyboardButton("Orders", callback_data="3"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            text = r"Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader\! There are a few things I can do:"
            self.reply_text(text, update.message, reply_markup, ParseMode.MARKDOWN_V2)
        except Exception:
            logger.exception("Failed to reply to /start command.")

    def killswitch(self, update: Update, context: CallbackContext):
        """Method to handle the /killswitch command"""
        request = baseRR.SetKillSwitchRequestMessage(True)
        self.mediator.set_kill_switch(request)
        self.reply_text(
            r"Kill switch, flipped. Awaiting confirmation...",
            update.message,
            None,
            ParseMode.HTML,
        )

    def help(self, update: Update, context: CallbackContext):
        """Method to handle the /help command"""
        self.reply_text(
            "Welcome to LoopTrader, I'm a Telegram bot here to help you manage your LoopTrader! There are a few things I can do: \r\n\n - <b>Push Notifications</b> will alert you to alerts you setup in your LoopTrader. \r\n - <b>/killswitch</b> will shutdown your LoopTrader. \r\n - <b>/balances</b> will display your latest account details. \r\n - <b>/orders</b> will display your open Orders. \r\n - <b>/positions</b> will show your open Positions. \r\n - <b>/performance</b> will show your daily P/L.",
            update.message,
            None,
            ParseMode.HTML,
        )

    def pause(self, update: Update, context: CallbackContext):
        """Method to handle the /pause command"""
        self.mediator.pause_bot()
        self.reply_text(
            r"Bot Paused",
            update.message,
            None,
            ParseMode.HTML,
        )

    def resume(self, update: Update, context: CallbackContext):
        """Method to handle the /resume command"""
        self.mediator.resume_bot()
        self.reply_text(
            r"Resuming Bot...",
            update.message,
            None,
            ParseMode.HTML,
        )

    def orders(self, update: Update, context: CallbackContext):
        """Method to handle the /orders command"""
        # Build Message
        msg = self.build_orders_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def positions(self, update: Update, context: CallbackContext):
        """Method to handle the /positions command"""
        # Build Message
        msg = self.build_positions_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def performance(self, update: Update, context: CallbackContext):
        """Method to handle the /positions command"""
        # Build Message
        msg = self.build_performance_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def tail(self, update: Update, context: CallbackContext):
        """Method to handle the /tail command"""
        # Error Handling
        try:
            if context.args is None:
                self.reply_text(
                    "Please enter a single positive integer.",
                    update.message,
                    None,
                    ParseMode.HTML,
                )
                return

            rows = int(context.args[0])

            if len(context.args) != 1 or rows <= 0:
                self.reply_text(
                    "There was an error with your input. Please enter a single positive integer.",
                    update.message,
                    None,
                    ParseMode.HTML,
                )
                return
        except Exception:
            self.reply_text(
                "There was an error with your input. Please enter a single positive integer.",
                update.message,
                None,
                ParseMode.HTML,
            )
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
        """Method to handle the /balances command"""
        # Build Message
        msg = self.build_balances_message()

        # Send Message
        self.reply_text(msg, update.message, None, ParseMode.HTML)

    def error(self, update, context: CallbackContext) -> None:
        """Method to handle errors occurring in the dispatcher"""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

        try:
            self.reply_text(
                r"An error occured, check the logs.",
                update.message,
                None,
                ParseMode.HTML,
            )
        except Exception:
            return

    def text(self, update: Update, context: CallbackContext):
        """Method to handle normal text"""
        self.reply_text(
            r"Sorry, I don't recognize your command.",
            update.message,
            None,
            ParseMode.HTML,
        )

    def button(self, update: Update, _: CallbackContext) -> None:
        """Method to handle /start command inline keyboard clicks"""

        if update.callback_query is None:
            return

        query = update.callback_query

        query.answer()

        if query.data == "1":
            msg = self.build_balances_message()
        elif query.data == "2":
            msg = self.build_positions_message()
        elif query.data == "3":
            msg = self.build_orders_message()

        try:
            self.edit_message_text(query, msg, ParseMode.HTML)
        except Exception:
            logger.exception("Telegram failed to callback.")

    # Helper Methods
    def add_handlers(self, dispatcher: Dispatcher):
        """Method to add handlers to our dispatcher"""
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("balances", self.balances))
        dispatcher.add_handler(CommandHandler("orders", self.orders))
        dispatcher.add_handler(CommandHandler("pause", self.pause))
        dispatcher.add_handler(CommandHandler("resume", self.resume))
        dispatcher.add_handler(CommandHandler("tail", self.tail, pass_args=True))
        dispatcher.add_handler(CommandHandler("positions", self.positions))
        dispatcher.add_handler(CommandHandler("performance", self.performance))
        dispatcher.add_handler(CommandHandler("killswitch", self.killswitch))
        dispatcher.add_handler(CallbackQueryHandler(self.button))

        # add an handler for normal text (not commands)
        dispatcher.add_handler(MessageHandler(Filters.text, self.text))

        # add an handler for errors
        dispatcher.add_error_handler(self.error, False)

    def build_balances_message(self) -> str:
        """Method to build the message string for the /balances command"""
        # Get Account
        request = GetAllAccountsRequestMessage(False, True)
        response = self.mediator.get_all_accounts(request)

        # Build Reply
        reply = r"Account Balances:"

        if response is None:
            reply += " \r\n No Accounts Found"
            return reply

        account: baseRR.GetAccountResponseMessage
        for account in response.accounts:
            reply += " \r\n<code>Account: {}</code>".format(account.accountnumber)
            if account is None or account.currentbalances is None:
                reply += " \r\n No Account Found"
                return reply

            # Build Reply
            reply += "\r\n - <b>Liquidation Value:</b> <code>${}</code>".format(
                "{:,.2f}".format(account.currentbalances.liquidationvalue)
            )
            reply += "\r\n - <b>Buying Power:</b> <code>${}</code>".format(
                "{:,.2f}".format(account.currentbalances.buyingpower)
            )

        return reply

    def build_performance_message(self) -> str:
        """Method to build the message string for the /performance command"""
        # Get Account
        request = GetAllAccountsRequestMessage(False, True)
        response = self.mediator.get_all_accounts(request)

        # Build Reply
        reply = r"Account Performance:"

        if response is None:
            reply += " \r\n No Accounts Found"
            return reply

        total = 0.0

        account: baseRR.GetAccountResponseMessage
        for account in response.accounts:
            reply += " \r\n<code>Account: {}</code>".format(account.accountnumber)
            for position in account.positions:
                total += position.currentdayprofitloss
                reply += " \r\n - <code>{}</code> > <code>${}</code>".format(
                    str(position.symbol),
                    "{:,.2f}".format(position.currentdayprofitloss),
                )

        reply += "\r\n\r\n<b>Total P&L:</b> <code>{}</code>".format(
            "{:,.2f}".format(total)
        )

        return reply

    def build_positions_message(self) -> str:
        """Method to build the message string for the /positions command"""
        # Get Account
        request = GetAllAccountsRequestMessage(False, True)
        response = self.mediator.get_all_accounts(request)

        # Build Reply
        reply = r"Account Positions:"

        if response is None:
            reply += " \r\n No Accounts Found"
            return reply

        account: baseRR.GetAccountResponseMessage
        for account in response.accounts:
            reply += " \r\n<code>Account: {}</code>".format(account.accountnumber)
            for position in account.positions:
                qty = position.shortquantity + position.longquantity
                reply += " \r\n <code>- {}x {} @ ${}</code>".format(
                    str(qty),
                    str(position.symbol),
                    "{:,.2f}".format(position.averageprice),
                )

        return reply

    def build_orders_message(self) -> str:
        """Method to build the message string for the /orders command"""
        # Get Account
        request = GetAllAccountsRequestMessage(True, False)
        response = self.mediator.get_all_accounts(request)

        # Build Reply
        reply = r"Open Orders:"

        if response is None:
            reply += " \r\n No Accounts Found"
            return reply

        account: baseRR.GetAccountResponseMessage
        for account in response.accounts:
            reply += " \r\n<code>Account: {}</code>".format(account.accountnumber)

            if account.orders is None:
                reply += " \r\n <code>- N/A</code>"
                continue

            for order in account.orders:
                if order.status in ["OPEN", "QUEUED"]:
                    price = 0 if order.price is None else order.price
                    formattedprice = "{:,.2f}".format(price)

                    leg = order.legs[0]

                    reply += " \r\n <code>- {}x {} {} @ ${}</code>".format(
                        str(order.quantity), leg.instruction, leg.symbol, formattedprice
                    )

        return reply

    def send_message(self, message: str, parsemode: Union[ParseMode, str]):
        """Wrapper method to send messages to a user"""
        try:
            bot = self.updater.bot
            bot.send_message(chat_id=self.chatid, text=message, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to send message.")

    @staticmethod
    def reply_text(
        text: str,
        message: Optional[Message],
        reply_markup: Union[InlineKeyboardMarkup, None],
        parsemode: Union[DefaultValue[str], str, None],
    ):
        """Wrapper method to send reply texts"""
        if message is None:
            return

        try:
            message.reply_text(
                text, reply_markup=reply_markup, quote=False, parse_mode=parsemode
            )
        except Exception:
            logger.exception("Telegram failed to reply.")

    @staticmethod
    def edit_message_text(
        query: CallbackQuery, msg: str, parsemode: Union[DefaultValue[str], str, None]
    ):
        """Wrapper method to edit message texts"""
        try:
            query.edit_message_text(text=msg, parse_mode=parsemode)
        except Exception:
            logger.exception("Telegram failed to callback.")
