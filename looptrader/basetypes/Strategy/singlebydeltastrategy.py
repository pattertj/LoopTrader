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


@attr.s(auto_attribs=True, eq=False, repr=False)
class SingleByDeltaStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for trading Cash-Secured Puts by Delta."""

    strategy_name: str = attr.ib(
        default="Sample Strategy", validator=attr.validators.instance_of(str)
    )
    underlying: str = attr.ib(
        default="$SPX.X", validator=attr.validators.instance_of(str)
    )
    portfolioallocationpercent: float = attr.ib(
        default=1.0, validator=attr.validators.instance_of(float)
    )
    buy_or_sell: str = attr.ib(
        default="SELL", validator=attr.validators.in_(["SELL", "BUY"])
    )
    put_or_call: str = attr.ib(
        default="PUT", validator=attr.validators.in_(["PUT", "CALL"])
    )
    targetdelta: float = attr.ib(
        default=-0.07, validator=attr.validators.instance_of(float)
    )
    mindelta: float = attr.ib(
        default=-0.03, validator=attr.validators.instance_of(float)
    )
    minimumdte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximumdte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    profittargetpercent: float = attr.ib(
        default=0.7, validator=attr.validators.instance_of(float)
    )
    maxlosscalcpercent: float = attr.ib(
        default=0.2, validator=attr.validators.instance_of(float)
    )
    openingorderloopseconds: int = attr.ib(
        default=20, validator=attr.validators.instance_of(int)
    )
    sleepuntil: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
    )
    minutesafteropendelay: int = attr.ib(
        default=3, validator=attr.validators.instance_of(int)
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
        hours = self.get_market_session_loop(dt.datetime.now())

        if hours is None:
            logger.error("Failed to get market hours, exiting and retrying.")
            return

        # If the next market session is not today, wait for it
        if hours.start.day != now.day:
            self.sleepuntil = (
                hours.start
                + dt.timedelta(minutes=self.minutesafteropendelay)
                - dt.timedelta(minutes=5)
            )
            logger.info(
                "Markets are closed until {}. Sleeping until {}".format(
                    hours.start, self.sleepuntil
                )
            )
            return

        # If Pre-Market
        if now < hours.start + dt.timedelta(minutes=self.minutesafteropendelay):
            self.process_pre_market()

        # If In-Market
        elif (
            hours.start + dt.timedelta(minutes=self.minutesafteropendelay)
            < now
            < hours.end
        ):
            self.process_open_market(hours.end, now)

        # If After-Hours
        elif hours.end < now:
            self.process_after_hours(hours.end, now)

    # Process Market
    def process_pre_market(self):
        """Pre-Market Trading Logic"""
        logger.debug("Processing Pre-Market.")

        # Get Next Open
        nextmarketsession = self.get_market_session_loop(dt.datetime.now())

        # Set sleepuntil
        self.sleepuntil = (
            nextmarketsession.start
            + dt.timedelta(minutes=self.minutesafteropendelay)
            - dt.timedelta(minutes=5)
        )

        logger.info(
            "Markets are closed until {}. Sleeping until {}".format(
                nextmarketsession.start
                + dt.timedelta(minutes=self.minutesafteropendelay),
                self.sleepuntil,
            )
        )

    def process_open_market(self, close: dt.datetime, now: dt.datetime):
        """Open Market Trading Logic"""
        logger.debug("Processing Open-Market")

        # Get the number of minutes till close
        minutestoclose = (close - now).total_seconds() / 60

        # Process Expiring Positions
        self.process_expiring_positions(minutestoclose)

        # Place New Orders
        self.place_new_orders_loop()

        # Process Closing Orders
        self.process_closing_orders(minutestoclose)

    def process_after_hours(self, close: dt.datetime, now: dt.datetime):
        """After-Hours Trading Logic"""
        logger.debug("Processing After-Hours")

        # Get the number of minutes since close
        minutesafterclose = (now - close).total_seconds() / 60

        # If beyond 5 min after close, exit
        if minutesafterclose > 5:
            # Get Next Open
            nextmarketsession = self.get_market_session_loop(
                dt.datetime.now() + dt.timedelta(days=1)
            )
            # Set sleepuntil
            self.sleepuntil = nextmarketsession.start - dt.timedelta(minutes=5)

            logger.info(
                "Markets are closed until {}. Sleeping until {}".format(
                    nextmarketsession.start, self.sleepuntil
                )
            )
            return

        # Build closing orders
        closingorders = self.build_closing_orders()

        if closingorders is None:
            logger.warning("No Closing Orders Built.")
            return None

        # Place closing Orders
        for order in closingorders:
            self.place_order(order)

        logger.info("Placed {} Closing Orders".format(len(closingorders)))

    def process_expiring_positions(self, minutestoclose):
        """Expiring Open Positions Trading Logic"""
        logger.debug("process_expiring_positions")
        # If there is more then 15min to the close, we can skip this logic.
        if minutestoclose > 15:
            return

        # Open expiring positions should be off-set to free-up buying power
        offsettingorders = self.build_offsetting_orders()

        # Place new order loop
        if offsettingorders is not None:
            for order in offsettingorders:
                self.place_order(order)

    def process_closing_orders(self, minutestoclose):
        """Closing Orders Trading Logic"""
        logger.debug("process_closing_orders")
        # If 15min from close
        if minutestoclose < 15:
            # Cancel closing orders
            cancellingorders = self.build_cancel_closing_orders()

            # Place cancel orders
            if cancellingorders is not None:
                for order in cancellingorders:
                    self.mediator.cancel_order(order)
        else:
            # Check for closing orders on open positions, and open orders if needed
            closingorders = self.build_closing_orders()

            # Place Closing Orders
            if closingorders is not None:
                for order in closingorders:
                    self.place_order(order)

    # Order Builders
    def build_offsetting_orders(self) -> list[baseRR.PlaceOrderRequestMessage]:
        """Offsetting orders for expiring positions Trading Logic"""
        logger.debug("build_offsetting_orders")
        return []
        # # Read positions
        # request = baseRR.GetAccountRequestMessage(False, True)
        # account = self.mediator.get_account(request)

        # # If not positions, nothing to offset
        # if account.positions is None:
        #     return

        # response = [baseRR.PlaceOrderResponseMessage]

        # # Check all positions
        # for position in account.positions:
        #     # Check if position is expiring today
        #     if position.expirationdate.date() == dt.datetime.now().date():
        #         if True:
        #             # Get today's option chain
        #             optionchainrequest = baseRR.GetOptionChainRequestMessage(symbol=self.underlying, contracttype='PUT', includequotes=True, optionrange='OTM', fromdate=dt.date.today(), todate=(dt.date.today()))
        #             optionchainresponse = self.mediator.get_option_chain(optionchainrequest)

        #             # Find a cheap option to offset
        #             # Build Order
        #             # Append to Reponse
        #             # response.append(offsetorder)

        # # Once we have reviewed all postiions, exit.
        # return response

    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        account = self.mediator.get_account(
            baseRR.GetAccountRequestMessage(self.strategy_name, False, True)
        )

        if account is None or not hasattr(account, "positions"):
            logger.error("Failed to get Account")
            return None

        # Get option chain
        chainrequest = self.build_option_chain_request()

        chain = self.mediator.get_option_chain(chainrequest)

        if chain is None:
            logger.error("Failed to get Option Chain.")
            return None

        # Should we even try?
        availbp = self.calculate_actual_buying_power(account)

        # Find next expiration
        if self.put_or_call == "PUT":
            expiration = self.get_next_expiration(chain.putexpdatemap)
        if self.put_or_call == "CALL":
            expiration = self.get_next_expiration(chain.callexpdatemap)

        # If no valid expirations, exit.
        if expiration is None:
            return None

        # Find best strike to trade
        strike = self.get_best_strike(
            expiration.strikes, availbp, account.currentbalances.liquidationvalue
        )

        # If no valid strikes, exit.
        if strike is None:
            return None

        # Calculate Quantity
        qty = self.calculate_order_quantity(
            strike.strike, availbp, account.currentbalances.liquidationvalue
        )

        # Calculate price
        formattedprice = self.format_order_price((strike.bid + strike.ask) / 2)

        # Return Order
        return self.build_opening_order_request(strike, qty, formattedprice)

    def build_option_chain_request(self) -> baseRR.GetOptionChainRequestMessage:
        """Builds the option chain request message.

        Returns:
            baseRR.GetOptionChainRequestMessage: Option chain request message
        """
        return baseRR.GetOptionChainRequestMessage(
            self.strategy_name,
            contracttype=self.put_or_call,
            fromdate=dt.date.today() + dt.timedelta(days=self.minimumdte),
            todate=dt.date.today() + dt.timedelta(days=self.maximumdte),
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
        )

    def build_opening_order_request(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        qty: int,
        price: float,
    ) -> baseRR.PlaceOrderRequestMessage:
        """Builds an order request to open a new postion

        Args:
            strike (baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike): The strike to trade
            qty (int): The number of contracts
            price (float): Contract Price

        Returns:
            baseRR.PlaceOrderRequestMessage: Order request message
        """
        # Build Leg
        leg = baseRR.PlaceOrderRequestMessage.Leg()
        leg.symbol = strike.symbol
        leg.assettype = "OPTION"
        leg.quantity = qty

        if self.buy_or_sell == "SELL":
            leg.instruction = "SELL_TO_OPEN"
        else:
            leg.instruction = "BUY_TO_OPEN"

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.strategy_name = self.strategy_name
        orderrequest.orderstrategytype = "SINGLE"
        orderrequest.duration = "GOOD_TILL_CANCEL"
        orderrequest.ordertype = "LIMIT"
        orderrequest.ordersession = "NORMAL"
        orderrequest.positioneffect = "OPENING"
        orderrequest.price = price
        orderrequest.legs = list[baseRR.PlaceOrderRequestMessage.Leg]()
        orderrequest.legs.append(leg)

        return orderrequest

    def build_cancel_closing_orders(
        self,
    ) -> Union[list[baseRR.CancelOrderRequestMessage], None]:
        """Trading Logic for cancelling closing order positions"""
        logger.debug("build_cancel_closing_orders")

        orderrequests = []

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(
            self.strategy_name, True, False
        )
        account = self.mediator.get_account(accountrequest)

        if account is None:
            logger.error("Failed to get Account.")
            return None

        # Look for open positions
        for order in account.orders:
            if order.status == "QUEUED" and order.legs[0].positioneffect == "CLOSING":
                orderrequest = baseRR.CancelOrderRequestMessage(
                    self.strategy_name, int(order.orderid)
                )
                orderrequests.append(orderrequest)

        return orderrequests

    def build_closing_orders(
        self,
    ) -> Union[list[baseRR.PlaceOrderRequestMessage], None]:
        """Trading Logic for building new Closing Order Request Messages"""
        logger.debug("build_closing_orders")

        orderrequests = []

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(self.strategy_name, True, True)
        account = self.mediator.get_account(accountrequest)

        if account is None:
            logger.error("Failed to get Account.")
            return None

        # Look for open positions
        for position in account.positions:
            if (
                position.underlyingsymbol == self.underlying
                and position.putcall == self.put_or_call
            ):
                close_exists = False

                # Look for closing Orders
                for order in account.orders:
                    # Do we have a match?
                    if (
                        order.status == "QUEUED"
                        and order.legs[0].symbol == position.symbol
                        and order.legs[0].instruction == "BUY_TO_CLOSE"
                    ):
                        # Does the quantity match?
                        if order.quantity == (
                            position.shortquantity + position.longquantity
                        ):
                            close_exists = True
                        else:
                            # Cancel current Order
                            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                                self.strategy_name, int(order.orderid)
                            )
                            self.mediator.cancel_order(cancelorderrequest)

                # Place a new Closing Order
                if not close_exists:
                    orderrequest = self.build_closing_order_request(position)
                    orderrequests.append(orderrequest)

        return orderrequests

    def build_closing_order_request(self, position: baseRR.AccountPosition):
        """Builds a closing order request message for a given position."""
        leg = baseRR.PlaceOrderRequestMessage.Leg()
        leg.symbol = position.symbol
        leg.assettype = "OPTION"
        leg.quantity = position.shortquantity

        if self.buy_or_sell == "SELL":
            leg.instruction = "BUY_TO_CLOSE"
        else:
            leg.instruction = "SELL_TO_CLOSE"

        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.strategy_name = self.strategy_name
        orderrequest.orderstrategytype = "SINGLE"
        orderrequest.duration = "GOOD_TILL_CANCEL"
        orderrequest.ordertype = "LIMIT"
        orderrequest.ordersession = "NORMAL"
        orderrequest.positioneffect = "CLOSING"
        orderrequest.price = self.truncate(
            self.format_order_price(
                position.averageprice * (1 - float(self.profittargetpercent))
            ),
            2,
        )
        orderrequest.legs = list[baseRR.PlaceOrderRequestMessage.Leg]()
        orderrequest.legs.append(leg)

        return orderrequest

    # Order Placers
    def place_new_orders_loop(self) -> None:
        """Looping Logic for placing new orders"""
        # Build Order
        neworder = self.build_new_order()

        # If neworder is None, exit.
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
            int(neworderresult.orderid), int(self.strategy_id), "NEW"
        )
        db_order_response = self.mediator.create_db_order(db_order_request)

        # If closing order, let the order ride, otherwise continue logic
        if orderrequest.positioneffect == "CLOSING":
            return True

        # Wait to let the Order process
        time.sleep(self.openingorderloopseconds)

        # Re-get the Order
        getorderrequest = baseRR.GetOrderRequestMessage(
            self.strategy_name, int(neworderresult.orderid)
        )
        processedorder = self.mediator.get_order(getorderrequest)

        if processedorder is None:
            # Log the Error
            logger.error(
                "Failed to get re-get placed order, ID: {}.".format(
                    neworderresult.orderid
                )
            )

            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                self.strategy_name, int(neworderresult.orderid)
            )
            self.mediator.cancel_order(cancelorderrequest)

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

        # Otherwise, add Position to the DB
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

    # Helpers
    def get_market_session_loop(
        self, date: dt.datetime
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Looping Logic for getting the next open session start and end times"""

        logger.debug("get_market_session_loop")

        request = baseRR.GetMarketHoursRequestMessage(
            self.strategy_name, market="OPTION", product="IND", datetime=date
        )

        # Get the market hours
        hours = self.mediator.get_market_hours(request)

        # If we didn't get hours, i.e. Weekend or if we are more than 15 minutes past market close, check tomorrow.
        # The 15 minute check is to allow the after-hours market logic to run
        if hours is None or hours.end + dt.timedelta(
            minutes=15
        ) < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.get_market_session_loop(date + dt.timedelta(days=1))
        return hours

    @staticmethod
    def check_for_closing_orders(
        symbol: str, orders: list[baseRR.AccountOrder]
    ) -> bool:
        """Checks a list of Orders for closing orders."""
        logger.debug("check_for_closing_orders")

        if orders == []:
            return False

        return any(
            order.status == "QUEUED"
            and order.legs[0].symbol == symbol
            and order.legs[0].instruction == "BUY_TO_CLOSE"
            for order in orders
        )

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

    def get_best_strike(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
        buyingpower: float,
        liquidationvalue: float,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_best_strike")
        # Set Variables
        bestpremium = float(0)
        beststrike = None

        # Iterate through strikes
        for strike, details in strikes.items():
            # Make sure strike delta is less then our target delta
            if (abs(details.delta) <= abs(self.targetdelta)) and (
                abs(details.delta) >= abs(self.mindelta)
            ):
                # Calculate the total premium for the strike based on our buying power
                qty = self.calculate_order_quantity(
                    strike, buyingpower, liquidationvalue
                )
                totalpremium = ((details.bid + details.ask) / 2) * qty

                # If the strike's premium is larger than our best premium, update it
                if totalpremium > bestpremium:
                    bestpremium = totalpremium
                    beststrike = details

        # Return the strike with the highest premium
        return beststrike

    def calculate_actual_buying_power(
        self, account: baseRR.GetAccountResponseMessage
    ) -> float:
        """Calculates the actual buying power based on the MaxLossCalcPercentage and current account balances.

        Args:
            account (baseRR.GetAccountResponseMessage): Account to calculate for

        Returns:
            float: Actual remaining buying power
        """
        usedbp = 0.0

        for position in account.positions:
            if (
                position.underlyingsymbol == self.underlying
                and position.putcall == self.put_or_call
            ):
                usedbp += self.calculate_position_buying_power(position)

        return account.currentbalances.liquidationvalue - usedbp

    def calculate_position_buying_power(
        self, position: baseRR.AccountPosition
    ) -> float:
        """Calculates the actual buying power for a given position

        Args:
            position (baseRR.AccountPosition): Account position to calculate

        Returns:
            float: Required buying power
        """
        return (
            position.strikeprice
            * 100
            * position.shortquantity
            * self.maxlosscalcpercent
        )

    def calculate_order_quantity(
        self, strike: float, buyingpower: float, liquidationvalue: float
    ) -> int:
        """Calculates the number of positions to open for a given account and strike."""
        logger.debug("calculate_order_quantity")

        # Calculate max loss per contract
        max_loss = strike * 100 * float(self.maxlosscalcpercent)

        # Calculate max buying power to use
        balance_to_risk = liquidationvalue * float(self.portfolioallocationpercent)

        remainingbalance = buyingpower - (liquidationvalue - balance_to_risk)

        # Calculate trade size
        trade_size = remainingbalance // max_loss

        # Log Values
        # logger.info(
        #     "Strike: {} BuyingPower: {} LiquidationValue: {} MaxLoss: {} BalanceToRisk: {} RemainingBalance: {} TradeSize: {} ".format(
        #         strike,
        #         buyingpower,
        #         liquidationvalue,
        #         max_loss,
        #         balance_to_risk,
        #         remainingbalance,
        #         trade_size,
        #     )
        # )

        # Return quantity
        return int(trade_size)

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
