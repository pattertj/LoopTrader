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


@attr.s(auto_attribs=True, eq=False, repr=False)
class SingleByDeltaStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for trading Cash-Secured Puts by Delta."""

    strategy: str = attr.ib(
        default="Sample Strategy", validator=attr.validators.instance_of(str)
    )
    underlying: str = attr.ib(
        default="$SPX.X", validator=attr.validators.instance_of(str)
    )
    portfolio_allocation_percent: float = attr.ib(
        default=1.0, validator=attr.validators.instance_of(float)
    )
    buy_or_sell: str = attr.ib(
        default="SELL", validator=attr.validators.in_(["SELL", "BUY"])
    )
    put_or_call: str = attr.ib(
        default="PUT", validator=attr.validators.in_(["PUT", "CALL"])
    )
    target_delta: float = attr.ib(
        default=-0.07, validator=attr.validators.instance_of(float)
    )
    min_delta: float = attr.ib(
        default=-0.03, validator=attr.validators.instance_of(float)
    )
    minimum_dte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximum_dte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    profit_target_percent: float = attr.ib(
        default=0.7, validator=attr.validators.instance_of(float)
    )
    max_loss_calc_percent: float = attr.ib(
        default=0.2, validator=attr.validators.instance_of(float)
    )
    opening_order_loop_seconds: int = attr.ib(
        default=20, validator=attr.validators.instance_of(int)
    )
    sleep_until: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
    )
    minutes_after_open_delay: int = attr.ib(
        default=3, validator=attr.validators.instance_of(int)
    )
    early_market_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    late_market_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=30),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    after_hours_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
    )

    # Core Strategy Process
    def process_strategy(self):
        """Main entry point to the strategy."""
        logger.debug("processstrategy")

        # Now
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # Check if we should be sleeping
        if now < self.sleep_until:
            return

        # Get Market Hours
        market_hours = self.get_next_market_hours(
            date=now, strategy_name=self.strategy_name
        )

        if market_hours is None:
            return

        # Calculate Market Boundaries
        core_market_open = market_hours.start + self.early_market_offset
        core_market_close = market_hours.end - self.late_market_offset
        after_hours_close = market_hours.end + self.after_hours_offset

        # If the next market open is not today, go to sleep until 60 minutes before market open to allow pre-market logic a chance.
        if market_hours.start.day != now.day:
            self.process_closed_market(market_hours.start - dt.timedelta(minutes=60))
            return

        # Check where we are
        if now < market_hours.start:
            # Process Pre-Market
            self.process_pre_market(market_hours.start)

        elif market_hours.start < now < core_market_open:
            # Process Pre-Core Market
            self.process_pre_core_market()

        elif core_market_open < now < core_market_close:
            # Process Core Market
            self.process_core_open_market(market_hours.end, now)

        elif core_market_close < now < market_hours.end:
            # Process After-Core Market
            self.process_core_open_market(market_hours.end, now)

        elif market_hours.end < now < after_hours_close:
            # Process After-Hours
            self.process_after_hours(market_hours.end, now)

        elif after_hours_close < now:
            # Process After-Market
            self.process_after_hours(market_hours.end, now)

        return

    ###############################
    ### Closed Market Functions ###
    ###############################
    def process_closed_market(self, market_open: dt.datetime):
        # Sleep until market opens
        self.sleep_until_market_open(market_open)
        return

    ############################
    ### Pre-Market Functions ###
    ############################
    def process_pre_market(self, market_open: dt.datetime):
        # Sleep until market opens
        self.sleep_until_market_open(market_open)
        return

    ############################
    ### Early Open Functions ###
    ############################
    def process_pre_core_market(self):
        # Nothing to do.
        pass

    #################################
    ### Core Open Hours Functions ###
    #################################
    def process_core_open_market(self, close: dt.datetime, now: dt.datetime):
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

    #############################
    ### After Hours Functions ###
    #############################
    def process_after_hours(self, close: dt.datetime, now: dt.datetime):
        """After-Hours Trading Logic"""
        logger.debug("Processing After-Hours")

        # Get the number of minutes since close
        minutesafterclose = (now - close).total_seconds() / 60

        # If beyond 5 min after close, exit
        if minutesafterclose > 5:
            # Sleep until market opens
            market = self.get_next_market_hours(
                date=now, strategy_name=self.strategy_name
            )

            if market is None:
                return

            self.sleep_until_market_open(market.start)
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
            fromdate=dt.date.today() + dt.timedelta(days=self.minimum_dte),
            todate=dt.date.today() + dt.timedelta(days=self.maximum_dte),
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
        )

    def build_opening_order_request(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        qty: int,
        price: float,
    ) -> baseRR.PlaceOrderRequestMessage:  # sourcery skip: class-extract-method
        """Builds an order request to open a new postion

        Args:
            strike (baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike): The strike to trade
            qty (int): The number of contracts
            price (float): Contract Price

        Returns:
            baseRR.PlaceOrderRequestMessage: Order request message
        """
        # Build Leg
        leg = baseModels.OrderLeg()
        leg.symbol = strike.symbol
        leg.asset_type = "OPTION"
        leg.quantity = qty
        leg.position_effect = "OPENING"

        if self.buy_or_sell == "SELL":
            leg.instruction = "SELL_TO_OPEN"
        else:
            leg.instruction = "BUY_TO_OPEN"

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"
        orderrequest.order.order_type = "LIMIT"
        orderrequest.order.session = "NORMAL"
        orderrequest.order.price = price
        orderrequest.order.legs = list[baseModels.OrderLeg]()
        orderrequest.order.legs.append(leg)

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

        # Look for open orders
        for order in account.orders:
            if (
                order.status in ["WORKING", "QUEUED"]
                and order.legs[0].position_effect == "CLOSING"
            ):
                orderrequest = baseRR.CancelOrderRequestMessage(
                    self.strategy_name, int(order.order_id)
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
                        order.legs != []
                        and order.status in ["WORKING", "QUEUED"]
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
                                self.strategy_name, int(order.order_id)
                            )
                            self.mediator.cancel_order(cancelorderrequest)

                # Place a new Closing Order
                if not close_exists:
                    orderrequest = self.build_closing_order_request(position)
                    orderrequests.append(orderrequest)

        return orderrequests

    def build_closing_order_request(self, position: baseRR.AccountPosition):
        """Builds a closing order request message for a given position."""
        leg = baseModels.OrderLeg()
        leg.symbol = position.symbol
        leg.asset_type = "OPTION"
        leg.quantity = position.shortquantity
        leg.position_effect = "CLOSING"

        if self.buy_or_sell == "SELL":
            leg.instruction = "BUY_TO_CLOSE"
        else:
            leg.instruction = "SELL_TO_CLOSE"

        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"
        orderrequest.order.order_type = "LIMIT"
        orderrequest.order.session = "NORMAL"
        orderrequest.order.price = self.truncate(
            self.format_order_price(
                position.averageprice * (1 - float(self.profit_target_percent))
            ),
            2,
        )
        orderrequest.order.legs = list[baseModels.OrderLeg]()
        orderrequest.order.legs.append(leg)

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
            or neworderresult.order_id is None
            or neworderresult.order_id == 0
        ):
            return False

        # Add Order to the DB
        # db_order_request = baseRR.CreateDatabaseOrderRequest(orderrequest.order)
        # db_order_response = self.mediator.create_db_order(db_order_request)

        # If closing order, let the order ride, otherwise continue logic
        for leg in orderrequest.order.legs:
            if leg.position_effect == "CLOSING":
                return True

        # Wait to let the Order process
        time.sleep(self.opening_order_loop_seconds)

        # Re-get the Order
        getorderrequest = baseRR.GetOrderRequestMessage(
            self.strategy_name, int(neworderresult.order_id)
        )
        processedorder = self.mediator.get_order(getorderrequest)

        if processedorder is None:
            # Log the Error
            logger.error(
                "Failed to get re-get placed order, ID: {}.".format(
                    neworderresult.order_id
                )
            )

            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                self.strategy_name, int(neworderresult.order_id)
            )
            self.mediator.cancel_order(cancelorderrequest)

            return False

        # If the order isn't filled
        if processedorder.order.status != "FILLED":
            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                self.strategy_name, int(neworderresult.order_id)
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

        self.send_notification(message)

        # If we got here, return success
        return True

    ########################
    ### Shared Functions ###
    ########################
    def sleep_until_market_open(self, datetime: dt.datetime):
        # Populate sleep-until variable
        self.sleep_until = datetime

        # Build Message
        message = (
            f"Markets are closed until {datetime}. Sleeping until {self.sleep_until}"
        )

        # Log our sleep
        logger.info(message)

        # Send a notification that we are sleeping
        self.send_notification(message)

    def get_market_hours(
        self, date: dt.datetime, strategy_name: str
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        # Build Request
        request = baseRR.GetMarketHoursRequestMessage(
            strategy_name, market="OPTION", product="IND", datetime=date
        )

        # Get Market Hours
        return self.mediator.get_market_hours(request)

    def get_next_market_hours(
        self,
        strategy_name: str,
        date: dt.datetime = dt.datetime.now().astimezone(dt.timezone.utc),
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        hours = self.get_market_hours(date, strategy_name)

        if hours is None or hours.end < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.get_next_market_hours(
                strategy_name, date + dt.timedelta(days=1)
            )

        return hours

    @staticmethod
    def check_for_closing_orders(symbol: str, orders: list[baseModels.Order]) -> bool:
        """Checks a list of Orders for closing orders."""
        logger.debug("check_for_closing_orders")

        if orders == []:
            return False

        return any(
            order.status in ["WORKING", "QUEUED"]
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
            if (abs(details.delta) <= abs(self.target_delta)) and (
                abs(details.delta) >= abs(self.min_delta)
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
            * self.max_loss_calc_percent
        )

    def calculate_order_quantity(
        self, strike: float, buyingpower: float, liquidationvalue: float
    ) -> int:
        """Calculates the number of positions to open for a given account and strike."""
        logger.debug("calculate_order_quantity")

        # Calculate max loss per contract
        max_loss = strike * 100 * float(self.max_loss_calc_percent)

        # Calculate max buying power to use
        balance_to_risk = liquidationvalue * float(self.portfolio_allocation_percent)

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

    ##############################
    ### Notification Functions ###
    ##############################
    def send_notification(self, message: str):
        # Append Strategy Prefix
        message = f"Strategy {self.strategy_name}({self.strategy_id}): {message}"

        # Build Request
        notification = baseRR.SendNotificationRequestMessage(message)

        # Send notification
        self.mediator.send_notification(notification)
