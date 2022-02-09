import datetime as dt
import logging
import logging.config
import math
import time
from typing import Union

import attr
import basetypes.Mediator.baseModels as baseModels
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
    width: float = attr.ib(
        default=float("inf"), validator=attr.validators.instance_of(float)
    )
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
    minutes_before_close: int = attr.ib(
        default=10, validator=attr.validators.instance_of(int)
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

        # If the next market session is not today, wait until 10 minutes before close
        if hours.start.day != now.day:
            self.sleepuntil = hours.end - dt.timedelta(
                minutes=self.minutes_before_close
            )
            logger.info(
                "Markets are closed until {}. Sleeping until {}".format(
                    hours.start, self.sleepuntil
                )
            )
            return

        # If Pre-Market
        if now < (hours.end - dt.timedelta(minutes=self.minutes_before_close)):
            self.process_pre_market()

        # If In-Market
        elif (
            (hours.end - dt.timedelta(minutes=self.minutes_before_close))
            < now
            < hours.end
        ):
            self.process_open_market()

    def process_pre_market(self):
        """Pre-Market Trading Logic"""
        logger.debug("Processing Pre-Market.")

        # Get Next Open
        nextmarketsession = self.get_market_session_loop(dt.datetime.now())

        # Set sleepuntil
        self.sleepuntil = nextmarketsession.end - dt.timedelta(
            minutes=self.minutes_before_close
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
        if self.place_order(neworder):
            return

        # Otherwise, try again
        self.place_new_orders_loop()

        return

    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(self.strategy_id, True, True)
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
            self.strategy_id,
            contracttype=self.put_or_call,
            fromdate=startdate,
            todate=enddate,
            symbol=self.underlying,
            includequotes=True,
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
        if expiration is None or expiration.strikes is None:
            return None

        # Get the short strike
        short_strike = self.get_short_strike(expiration.strikes)

        # If no short strike, exit.
        if short_strike is None:
            return None

        long_strike = self.get_long_strike(expiration.strikes, short_strike)

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
            short_strike.bid + short_strike.ask - long_strike.bid - long_strike.ask
        ) / 2
        formattedprice = self.format_order_price(price)

        # Build Short Leg
        shortleg = self.build_leg(short_strike, qty, "SELL")

        # Build Long Leg
        longleg = self.build_leg(long_strike, qty, "BUY")

        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order = baseModels.Order()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"
        if self.buy_or_sell == "SELL":
            orderrequest.order.order_type = "NET_CREDIT"
        else:
            orderrequest.order.order_type = "NET_DEBIT"
        orderrequest.order.session = "NORMAL"
        orderrequest.order.price = formattedprice
        orderrequest.order.legs = list[baseModels.OrderLeg]()
        orderrequest.order.legs.append(shortleg)
        orderrequest.order.legs.append(longleg)

        return orderrequest

    def build_leg(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        quantity: int,
        buy_or_sell: str,
    ) -> baseModels.OrderLeg:
        leg = baseModels.OrderLeg()
        leg.symbol = strike.symbol
        leg.asset_type = "OPTION"
        leg.quantity = quantity
        leg.position_effect = "OPENING"

        leg.instruction = "SELL_TO_OPEN" if buy_or_sell == "SELL" else "BUY_TO_OPEN"
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

        if self.width == float("inf"):
            return True

        # Check if we have positions on already that expire today.
        # If nothing is expiring and no tradable balance, exit.
        # If we are expiring, continue trying to place a trade
        # If we have a tradable balance, continue trying to place a trade
        if any(
            position.underlyingsymbol == self.underlying
            and position.expirationdate.date() != dt.date.today()
            for position in account.positions
        ):
            return False

        # Check if we have positions on already that expire today.
        expiring_day = any(
            position.underlyingsymbol == self.underlying
            and position.expirationdate.date() == dt.date.today()
            for position in account.positions
        )

        # Check Available Balance
        tradable_today = (
            account.currentbalances.liquidationvalue * self.portfolioallocationpercent
        ) > (self.width * 100) and account.currentbalances.buyingpower > (
            self.width * 100
        )

        return expiring_day or tradable_today

    def place_order(self, orderrequest: baseRR.PlaceOrderRequestMessage) -> bool:
        """Method for placing new Orders and handling fills"""
        # Try to place the Order
        neworderresult = self.mediator.place_order(orderrequest)

        # If the order placement fails, exit the method.
        if (
            neworderresult is None
            or neworderresult.order_id is None
            or neworderresult.order_id == 0
        ):
            return False

        # Add Order to the DB
        # db_order_request = baseRR.CreateDatabaseOrderRequest(orderrequest.order)
        # db_order_response = self.mediator.create_db_order(db_order_request)

        # Wait to let the Order process
        time.sleep(self.openingorderloopseconds)

        # Fetch the Order status
        getorderrequest = baseRR.GetOrderRequestMessage(
            self.strategy_id, int(neworderresult.order_id)
        )
        processedorder = self.mediator.get_order(getorderrequest)

        if processedorder is None:
            return False

        # If the order isn't filled
        if processedorder.order.status != "FILLED":
            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                self.strategy_id, int(neworderresult.order_id)
            )
            self.mediator.cancel_order(cancelorderrequest)

            # Return failure to fill order
            return False

        # Otherwise, add Position to the DB
        for leg in orderrequest.order.legs:
            db_position_request = baseRR.CreateDatabaseOrderRequest(
                processedorder.order
            )
        self.mediator.create_db_order(db_position_request)

        # Send a notification
        message = "Sold:<code>"

        for leg in orderrequest.order.legs:
            message += "\r\n - {}x {} @ ${}".format(
                str(leg.quantity),
                str(leg.symbol),
                "{:,.2f}".format(orderrequest.order.price),
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
            self.strategy_id, market="OPTION", product="EQO", datetime=date
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

        if expirations is None or not expirations:
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
        first_strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_best_strike")

        best_strike = 0.0

        # If Max Width, find cheapest long
        if self.width == float("inf"):

            if self.buy_or_sell == "BUY":
                logger.error("Cannot buy a max-width spread.")
                return None

            best_mid = float("inf")

            for strike, detail in strikes.items():
                mid = (detail.bid + detail.ask) / 2

                # If the mid-price is lower, use it
                if 0.00 < mid < best_mid:
                    best_strike = strike
                    best_mid = mid
                # If we're selling a PUT and the mid price is the same, but the strike is higher, use it.
                elif (self.put_or_call == "PUT") and (
                    (mid == best_mid) and (best_strike < strike < first_strike.strike)
                ):
                    best_strike = strike
                    best_mid = mid
                # If we're selling a CALL and the mid price is the same, but the strike is lower, use it.
                elif self.put_or_call == "CALL" and (
                    (mid == best_mid) and (best_strike > strike > first_strike.strike)
                ):
                    best_strike = strike
                    best_mid = mid

        # Otherwise get closest strike to the set width
        else:
            best_delta = 1000000.0
            new_strike = first_strike.strike - self.width

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

        # Calculate max buying power to use
        balance_to_risk = account_balance.liquidationvalue * float(
            self.portfolioallocationpercent
        )

        # Calculate max loss per contract
        if self.width == float("inf"):
            # Calculate max loss per contract
            max_loss = shortstrike * 100 * 0.2

            trading_power = account_balance.buyingpower - (
                account_balance.liquidationvalue - balance_to_risk
            )

        else:
            max_loss = abs(shortstrike - longstrike) * 100

            trading_power = min(balance_to_risk, account_balance.buyingpower)

        # Calculate trade size
        trade_size = trading_power // max_loss

        # Log Values
        logger.info(
            "Short Strike: {} Long Strike: {} BuyingPower: {} LiquidationValue: {} MaxLoss: {} BalanceToRisk: {} TradingPower: {} TradeSize: {} ".format(
                shortstrike,
                longstrike,
                account_balance.buyingpower,
                account_balance.liquidationvalue,
                max_loss,
                balance_to_risk,
                trading_power,
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
