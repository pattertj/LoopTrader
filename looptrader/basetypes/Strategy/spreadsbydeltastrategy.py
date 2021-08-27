import datetime as dt
import logging
import logging.config
import math
import time
from typing import Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Component.abstractComponent import Component
from basetypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True, eq=False)
class SpreadsByDeltaStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for trading Option Spreads by Delta."""

    strategy_name: str = attr.ib(
        default="Sample Spread Strategy", validator=attr.validators.instance_of(str)
    )
    underlying: str = attr.ib(
        default="$SPX.X", validator=attr.validators.instance_of(str)
    )
    portfolioallocationpercent: float = attr.ib(
        default=0.50, validator=attr.validators.instance_of(float)
    )
    put_or_call: str = attr.ib(
        default="PUT", validator=attr.validators.in_(["PUT", "CALL"])
    )
    buy_or_sell: str = attr.ib(
        default="SELL", validator=attr.validators.in_(["SELL", "BUY"])
    )
    targetdelta: float = attr.ib(
        default=-0.10, validator=attr.validators.instance_of(float)
    )
    width: float = attr.ib(default=70.0, validator=attr.validators.instance_of(float))
    minimumdte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximumdte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    openingorderloopseconds: int = attr.ib(
        default=60, validator=attr.validators.instance_of(int)
    )
    sleepuntil: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
    )

    # Core Strategy Process
    def process_strategy(self):
        """Main entry point to the strategy."""
        logger.debug("processstrategy")

        # Get current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # Check if should be sleeping
        if now < self.sleepuntil:
            logger.debug("Markets Closed. Sleeping until {}".format(self.sleepuntil))
            return

        # Check market hours
        hours = self.get_market_session_loop(now)

        if hours is None:
            logger.error("Failed to get market hours, exiting and retrying.")
            return

        # If the next market session is not today, wait until 30minutes before close
        if hours.start.day != now.day:
            self.sleepuntil = hours.end - dt.timedelta(minutes=30)
            logger.info(
                "Markets are closed until {}. Sleeping until {}".format(
                    hours.start, self.sleepuntil
                )
            )
            return

        # If Pre-Market
        if now < (hours.end - dt.timedelta(minutes=30)):
            self.process_pre_market()

        # If In-Market
        elif (hours.end - dt.timedelta(minutes=30)) < now < hours.end:
            self.process_open_market()

    def process_pre_market(self):
        """Pre-Market Trading Logic"""
        logger.debug("Processing Pre-Market.")

        # Get Next Open
        nextmarketsession = self.get_market_session_loop(dt.datetime.now())

        # Set sleepuntil
        self.sleepuntil = (
            nextmarketsession.end - dt.timedelta(minutes=30) - dt.timedelta(minutes=5)
        )

        logger.info(
            "Markets are closed until {}. Sleeping until {}".format(
                nextmarketsession.start,
                self.sleepuntil,
            )
        )

    def process_open_market(self):
        """Open Market Trading Logic"""
        logger.debug("Processing Open-Market")

        # Place New Orders
        self.place_new_orders_loop()

    # Order Placers
    def place_new_orders_loop(self) -> None:
        """Looping Logic for placing new orders"""
        # Build Order
        neworder = self.build_new_order()

        # If there isn't an order, exit.
        if neworder is None:
            return

        # Place the order and check the result
        result = self.place_order(neworder)

        # If successful, return
        if result:
            return

        # Otherwise, try again
        self.place_new_orders_loop()

        return

    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(self.strategy_name, True, True)
        account = self.mediator.get_account(accountrequest)

        if account is None:
            logger.error("Failed to get Account")
            return None

        # Check if we should place a trade
        if not self.build_new_order_precheck(account):
            logger.info("Buying Power too low.")
            return None

        # Calculate trade date
        startdate = dt.date.today() + dt.timedelta(days=self.minimumdte)
        enddate = dt.date.today() + dt.timedelta(days=self.maximumdte)

        # Get option chain
        chainrequest = baseRR.GetOptionChainRequestMessage(
            self.strategy_name,
            contracttype=self.put_or_call,
            fromdate=startdate,
            todate=enddate,
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
        )

        chain = self.mediator.get_option_chain(chainrequest)

        if chain is None:
            return None

        # Find expiration to trade
        if self.put_or_call == "PUT":
            expiration = self.get_next_expiration(chain.putexpdatemap)
        else:
            expiration = self.get_next_expiration(chain.callexpdatemap)

        # If no valid expirations, exit.
        if expiration is None:
            return None

        # Get the short strike
        short_strike = self.get_short_strike(expiration.strikes)

        # If no short strike, exit.
        if short_strike is None:
            return None

        long_strike = self.get_long_strike(expiration.strikes, short_strike.strike)

        # If no valid long strike, exit.
        if long_strike is None:
            return None

        # Calculate Quantity
        qty = self.calculate_order_quantity(
            short_strike.strike, long_strike.strike, account.currentbalances
        )

        # Return Order
        return self.build_order_request(short_strike, long_strike, qty)

    def build_order_request(
        self,
        short_strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        long_strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        qty: int,
    ) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        # If no valid qty, exit.
        if qty is None or qty <= 0:
            return None

        # Calculate price
        price = (
            short_strike.bid + short_strike.ask - (long_strike.bid + long_strike.ask)
        ) / 2
        formattedprice = self.format_order_price(price)

        # Build Short Leg
        shortleg = self.build_leg(short_strike, qty, "SELL")

        # Build Long Leg
        longleg = self.build_leg(long_strike, qty, "BUY")

        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.strategy_name = self.strategy_name
        orderrequest.orderstrategytype = "SINGLE"
        orderrequest.duration = "GOOD_TILL_CANCEL"
        if self.buy_or_sell == "SELL":
            orderrequest.ordertype = "NET_CREDIT"
        else:
            orderrequest.ordertype = "NET_DEBIT"
        orderrequest.ordersession = "NORMAL"
        orderrequest.positioneffect = "OPENING"
        orderrequest.price = formattedprice
        orderrequest.legs = list[baseRR.PlaceOrderRequestMessage.Leg]()
        orderrequest.legs.append(shortleg)
        orderrequest.legs.append(longleg)

        return orderrequest

    def build_leg(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        quantity: int,
        buy_or_sell: str,
    ) -> baseRR.PlaceOrderRequestMessage.Leg:
        leg = baseRR.PlaceOrderRequestMessage.Leg()
        leg.symbol = strike.symbol
        leg.assettype = "OPTION"
        leg.quantity = quantity

        if buy_or_sell == "SELL":
            leg.instruction = "SELL_TO_OPEN"
        else:
            leg.instruction = "BUY_TO_OPEN"

        return leg

    def build_leg_instruction(self, short_or_long: str) -> str:
        if (
            short_or_long == "short"
            and self.buy_or_sell == "SELL"
            or short_or_long != "short"
            and self.buy_or_sell != "SELL"
        ):
            return "SELL_TO_OPEN"
        else:
            return "BUY_TO_OPEN"

    def build_new_order_precheck(
        self, account: baseRR.GetAccountResponseMessage
    ) -> bool:
        # Check if we have positions on already that expire today.
        expiring_day = any(
            position.underlyingsymbol == self.underlying
            and position.expirationdate.date() == dt.date.today()
            for position in account.positions
        )

        # Check if we have positions on already that expire today.
        nonexpiring = any(
            position.underlyingsymbol == self.underlying
            and position.expirationdate.date() != dt.date.today()
            for position in account.positions
        )

        # Check Available Balance
        tradable_today = (
            account.currentbalances.liquidationvalue * self.portfolioallocationpercent
        ) > (self.width * 100) and account.currentbalances.buyingpower > (
            self.width * 100
        )

        # If nothing is expiring and no tradable balance, exit.
        # If we are expiring, continue trying to place a trade
        # If we have a tradable balance, continue trying to place a trade
        if nonexpiring:
            return False
        else:
            return expiring_day or tradable_today

    def place_order(self, orderrequest: baseRR.PlaceOrderRequestMessage) -> bool:
        """Method for placing new Orders and handling fills"""
        # Try to place the Order
        neworderresult = self.mediator.place_order(orderrequest)

        # If the order placement fails, exit the method.
        if (
            neworderresult is None
            or neworderresult.orderid is None
            or neworderresult.orderid == 0
        ):
            return False

        # Add Order to the DB
        db_order_request = baseRR.CreateDatabaseOrderRequest(
            neworderresult.orderid, self.strategy_id, "NEW"
        )
        db_order_response = self.mediator.create_db_order(db_order_request)

        # Wait to let the Order process
        time.sleep(self.openingorderloopseconds)

        # Fetch the Order status
        getorderrequest = baseRR.GetOrderRequestMessage(
            self.strategy_name, int(neworderresult.orderid)
        )
        processedorder = self.mediator.get_order(getorderrequest)

        if processedorder is None:
            return False

        # If the order isn't filled
        if processedorder.status != "FILLED":
            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                self.strategy_name, int(neworderresult.orderid)
            )
            self.mediator.cancel_order(cancelorderrequest)

            # Return failure to fill order
            return False

        # Add the position to the DB
        if db_order_response is not None:
            for leg in orderrequest.legs:
                db_position_request = baseRR.CreateDatabasePositionRequest(
                    self.strategy_id,
                    leg.symbol,
                    leg.quantity,
                    True,
                    db_order_response.order_id,
                    0,
                )
                self.mediator.create_db_position(db_position_request)

        # Send a notification
        message = "Sold:<code>"

        for leg in orderrequest.legs:
            message += "\r\n - {}x {} @ ${}".format(
                str(leg.quantity), str(leg.symbol), "{:,.2f}".format(orderrequest.price)
            )

        message += "</code>"

        notification = baseRR.SendNotificationRequestMessage(message)

        self.mediator.send_notification(notification)

        # If we got here, return success
        return True

    # Market Hours Functions
    def get_market_session_loop(
        self, date: dt.datetime
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Looping Logic for getting the next open session start and end times"""
        logger.debug("get_market_session_loop")

        request = baseRR.GetMarketHoursRequestMessage(
            self.strategy_name, market="OPTION", product="EQO", datetime=date
        )

        hours = self.mediator.get_market_hours(request)

        if hours is None or hours.end < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.get_market_session_loop(date + dt.timedelta(days=1))

        return hours

    # Option Chain Functions
    @staticmethod
    def get_next_expiration(
        expirations: list[baseRR.GetOptionChainResponseMessage.ExpirationDate],
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate, None]:
        """Checks an option chain response for the next expiration date."""
        logger.debug("get_next_expiration")

        if expirations is None or expirations == []:
            logger.error("No expirations provided.")
            return None

        # Initialize min DTE to infinity
        mindte = math.inf

        # loop through expirations and find the minimum DTE
        for expiration in expirations:
            dte = expiration.daystoexpiration
            if dte < mindte:
                mindte = dte
                minexpiration = expiration

        # Return the min expiration
        return minexpiration

    def get_short_strike(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_best_strike")

        # Set Variables
        best_price = float(0)
        best_strike = None

        # Iterate through strikes
        for details in strikes.values():
            if details.delta is None or details.delta == "NaN":
                continue

            # Make sure strike delta is less then our target delta
            if abs(details.delta) <= abs(self.targetdelta):
                # Calculate the total premium for the strike based on our buying power
                mid_price = (details.bid + details.ask) / 2
                if mid_price > best_price:
                    best_strike = details
                    best_price = mid_price

        # Return the strike with the highest premium, under our delta
        return best_strike

    def get_long_strike(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
        short_strike: float,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_best_strike")

        new_strike = short_strike - self.width

        best_strike = 0.0
        best_delta = 1000000.0

        for strike in strikes:
            delta = strike - new_strike
            if abs(delta) < best_delta:
                best_strike = strike
                best_delta = abs(delta)

        # Return the strike
        return strikes[best_strike]

    def calculate_order_quantity(
        self,
        shortstrike: float,
        longstrike: float,
        account_balance: baseRR.AccountBalance,
    ) -> int:
        """Calculates the number of positions to open for a given account and strike."""
        logger.debug("calculate_order_quantity")

        # Calculate max loss per contract
        max_loss = abs(shortstrike - longstrike) * 100

        # Calculate max buying power to use
        balance_to_risk = account_balance.liquidationvalue * float(
            self.portfolioallocationpercent
        )

        remainingbalance = account_balance.buyingpower

        # Calculate trade size
        trade_size = remainingbalance // max_loss

        # Log Values
        logger.info(
            "Short Strike: {} Long Strike: {} BuyingPower: {} LiquidationValue: {} MaxLoss: {} BalanceToRisk: {} RemainingBalance: {} TradeSize: {} ".format(
                shortstrike,
                longstrike,
                account_balance.buyingpower,
                account_balance.liquidationvalue,
                max_loss,
                balance_to_risk,
                remainingbalance,
                trade_size,
            )
        )

        # Return quantity
        return int(trade_size)

    # Helpers
    def format_order_price(self, price: float) -> float:
        """Formats a price according to brokerage rules."""
        logger.debug("format_order_price")

        base = 0.1 if price > 3 else 0.05
        return self.truncate(base * round(price / base), 2)

    @staticmethod
    def truncate(number: float, digits: int) -> float:
        """Truncates a float to a specified number of digits."""
        logger.debug("truncate")
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper
