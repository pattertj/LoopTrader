import datetime as dt
import logging
import logging.config
import math
import time
from typing import Union

import attr
import basetypes.Mediator.baseModels as baseModels
import basetypes.Mediator.reqRespTypes as baseRR
import basetypes.Strategy.helpers as helpers
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
        default=dt.timedelta(minutes=10),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    after_hours_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    use_vollib_for_greeks: bool = attr.ib(
        default=True, validator=attr.validators.instance_of(bool)
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
        market_hours = self.get_next_market_hours(date=now)

        if market_hours is None:
            return

        # If the next market open is not today, go to sleep until 60 minutes before market open to allow pre-market logic a chance.
        if market_hours.start.day != now.day:
            self.process_closed_market(market_hours.start - dt.timedelta(minutes=60))
            return

        # Calculate Market Boundaries
        core_market_open = market_hours.start + self.early_market_offset
        core_market_close = market_hours.end - self.late_market_offset
        after_hours_close = market_hours.end + self.after_hours_offset

        self.process_core_market()

        # Check where we are
        if now < market_hours.start:
            # Process Pre-Market
            self.process_pre_market(market_hours.start)

        elif market_hours.start < now < core_market_open:
            # Process Pre-Core Market
            self.process_early_core_market()

        elif core_market_open < now < core_market_close:
            # Process Core Market
            self.process_core_market()

        elif core_market_close < now < market_hours.end:
            # Process After-Core Market
            self.process_late_core_market()

        elif market_hours.end < now < after_hours_close:
            # Process After-Hours
            self.process_after_hours(market_hours.end, now)

        elif after_hours_close < now:
            # Process After-Market
            self.process_after_market()

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
    ### Early Core Functions ###
    ############################
    def process_early_core_market(self):
        # Nothing to do.
        pass

    #############################
    ### Core Market Functions ###
    #############################
    def process_core_market(self):
        # Check for open Orders
        current_orders = self.get_current_orders()
        has_open_orders = len(current_orders) > 0

        # Logger
        logger.debug(
            f"Strategy {self.strategy_name} Has {'' if has_open_orders else 'No '}Open Orders"
        )

        # If no open orders, open a new one.
        if not has_open_orders:
            self.place_new_orders_loop()

    ############################
    ### Late Core Functions ###
    ############################
    def process_late_core_market(self):
        # Check for open Orders
        current_orders = self.get_current_orders()
        has_open_orders = len(current_orders) > 0

        # Logger
        logger.debug(
            f"Strategy {self.strategy_name} Has {'' if has_open_orders else 'No '}Open Orders"
        )

        # If no open orders, open a new one.
        if not has_open_orders:
            self.place_new_orders_loop()

        # Else, check expirations
        else:
            for order in current_orders:
                # Check if the position expires today
                if order.legs[0].expiration_date == dt.date.today():
                    # Offset
                    self.place_offsetting_order_loop(order.quantity)

                    # Open a new position
                    self.place_new_orders_loop()

    #############################
    ### After Hours Functions ###
    #############################
    def process_after_hours(self, close: dt.datetime, now: dt.datetime):
        """After-Hours Trading Logic"""
        # Check for open Orders
        current_orders = self.get_current_orders()
        has_open_orders = len(current_orders) > 0

        # Logger
        logger.debug(
            f"Strategy {self.strategy_name} Has {'' if has_open_orders else 'No '}Open Orders"
        )

        # If no open orders, open a new one.
        if not has_open_orders:
            self.place_new_orders_loop()

    ##############################
    ### After Market Functions ###
    ##############################
    def process_after_market(self):
        # Sleep until market opens
        market = self.get_next_market_hours()

        self.sleep_until_market_open(market.start)
        return

    ######################
    ### Order Builders ###
    ######################
    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        account = self.mediator.get_account(
            baseRR.GetAccountRequestMessage(self.strategy_id, False, True)
        )

        if account is None or not hasattr(account, "positions"):
            logger.error("Failed to get Account")
            return None

        # Get option chain
        min_date = dt.date.today() + dt.timedelta(days=self.minimum_dte)
        max_date = dt.date.today() + dt.timedelta(days=self.maximum_dte)
        chainrequest = self.build_option_chain_request(min_date, max_date)

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
            expiration.strikes,
            availbp,
            account.currentbalances.liquidationvalue,
            expiration.daystoexpiration,
            chain.underlyinglastprice,
            chain.volatility,
        )

        # If no valid strikes, exit.
        if strike is None:
            return None

        # Calculate Quantity
        qty = self.calculate_order_quantity(
            strike.strike, availbp, account.currentbalances.liquidationvalue
        )

        # Calculate price
        formattedprice = helpers.format_order_price((strike.bid + strike.ask) / 2)

        # Return Order
        return self.build_opening_order_request(strike, qty, formattedprice)

    def build_offsetting_order(
        self, qty: int
    ) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building Offsetting Order Request Messages"""
        logger.debug("build_offsetting_order")

        # Get option chain
        chainrequest = self.build_option_chain_request(dt.date.today(), dt.date.today())
        chain = self.mediator.get_option_chain(chainrequest)

        if chain is None:
            logger.error("Failed to get Option Chain.")
            return None

        # Find next expiration
        if self.put_or_call == "CALL":
            expiration = chain.callexpdatemap[0]
        elif self.put_or_call == "PUT":
            expiration = chain.putexpdatemap[0]

        # Find best strike to trade
        strike = self.get_offsetting_strike(expiration.strikes)

        if strike is None:
            logger.error("Failed to get Offsetting Strike.")
            return None

        # Return Order
        return self.build_opening_order_request(
            strike, qty, strike.ask, offsetting=True
        )

    def build_opening_order_request(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        qty: int,
        price: float,
        offsetting: bool = False,
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

        if (
            offsetting
            and self.buy_or_sell == "SELL"
            or not offsetting
            and self.buy_or_sell != "SELL"
        ):
            leg.instruction = "BUY_TO_OPEN"
        else:
            leg.instruction = "SELL_TO_OPEN"

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order = baseModels.Order()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"
        orderrequest.order.order_type = "LIMIT"
        orderrequest.order.session = "NORMAL"
        orderrequest.order.price = price
        orderrequest.order.legs = list[baseModels.OrderLeg]()
        orderrequest.order.legs.append(leg)

        return orderrequest

    def new_build_closing_order(
        self, original_order: baseModels.Order
    ) -> baseRR.PlaceOrderRequestMessage:
        """Builds a closing order request message for a given position."""
        leg = baseModels.OrderLeg()
        leg.symbol = original_order.legs[0].symbol
        leg.asset_type = "OPTION"
        leg.quantity = original_order.legs[0].quantity
        leg.position_effect = "CLOSING"

        if original_order.legs[0].instruction == "SELL_TO_OPEN":
            leg.instruction = "BUY_TO_CLOSE"
        else:
            leg.instruction = "SELL_TO_CLOSE"

        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order = baseModels.Order()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"
        orderrequest.order.order_type = "LIMIT"
        orderrequest.order.session = "NORMAL"
        orderrequest.order.price = helpers.truncate(
            helpers.format_order_price(
                original_order.price * (1 - float(self.profit_target_percent))
            ),
            2,
        )
        orderrequest.order.legs = list[baseModels.OrderLeg]()
        orderrequest.order.legs.append(leg)

        return orderrequest

    #####################
    ### Order Placers ###
    #####################
    def cancel_order(self, order_id: int):
        # Build Request
        cancelorderrequest = baseRR.CancelOrderRequestMessage(
            self.strategy_id, int(order_id)
        )
        # Send Request
        self.mediator.cancel_order(cancelorderrequest)

    def place_offsetting_order_loop(self, qty: int) -> None:
        # Build Order
        offsetting_order_request = self.build_offsetting_order(qty)

        # If neworder is None, exit.
        if offsetting_order_request is None:
            return

        # Place the order and check the result
        result = self.place_order(offsetting_order_request)

        # If successful, return
        if result:
            return

        # Otherwise, try again
        self.place_offsetting_order_loop(qty)

        return

    def place_new_orders_loop(self) -> None:
        """Looping Logic for placing new orders"""
        # Build Order
        new_order_request = self.build_new_order()

        # If neworder is None, exit.
        if new_order_request is None:
            return

        # Place the order and check the result
        result = self.place_order(new_order_request)

        # If successful, return
        if result:
            closing_order = self.new_build_closing_order(new_order_request.order)
            self.place_order(closing_order)
            return

        # Otherwise, try again
        self.place_new_orders_loop()

        return

    def place_order(self, orderrequest: baseRR.PlaceOrderRequestMessage) -> bool:
        """Method for placing new Orders and handling fills"""
        # Try to place the Order
        new_order_result = self.mediator.place_order(orderrequest)

        # If the order placement fails, exit the method.
        if (
            new_order_result is None
            or new_order_result.order_id is None
            or new_order_result.order_id == 0
        ):
            return False

        # Wait to let the Order process
        time.sleep(self.opening_order_loop_seconds)

        # Re-get the Order
        order_request = baseRR.GetOrderRequestMessage(
            self.strategy_id, int(new_order_result.order_id)
        )
        processed_order = self.mediator.get_order(order_request)

        if processed_order is None:
            # Log the Error
            logger.error(
                f"Failed to get re-get placed order, ID: {new_order_result.order_id}."
            )

            # Cancel it
            self.cancel_order(new_order_result.order_id)

            return False

        # If closing order, add Order to DB and let the order ride, otherwise continue logic
        for leg in processed_order.order.legs:
            if leg.position_effect == "CLOSING":
                # Add Position to the DB
                db_position_request = baseRR.CreateDatabaseOrderRequest(
                    processed_order.order
                )
                self.mediator.create_db_order(db_position_request)
                # Return Success
                return True

        # If the order isn't filled
        if processed_order.order.status != "FILLED":
            # Cancel it
            self.cancel_order(new_order_result.order_id)

            # Return failure to fill order
            return False

        # Otherwise, add Position to the DB
        db_position_request = baseRR.CreateDatabaseOrderRequest(processed_order.order)
        self.mediator.create_db_order(db_position_request)

        # Send a notification
        message = "Sold:<code>"

        for leg in orderrequest.order.legs:
            message += (
                f"\r\n - {leg.quantity}x {leg.symbol} @ ${orderrequest.order.price:.2f}"
            )
        message += "</code>"

        helpers.send_notification(
            message, self.strategy_name, self.strategy_id, self.mediator
        )

        # If we got here, return success
        return True

    ########################
    ### Shared Functions ###
    ########################
    def get_current_orders(self) -> list[baseModels.Order]:
        current_orders = []  # type: list[baseModels.Order]

        # Read DB Orders
        open_orders_request = baseRR.ReadOpenDatabaseOrdersRequest(self.strategy_id)
        open_orders = self.mediator.read_active_orders(open_orders_request)

        if open_orders is None:
            logger.error("Read_Open_Orders failed. Please check the logs.")
            return current_orders

        # Iterate through any open Orders
        for order in open_orders.orders:
            # Get latest status
            get_order_req = baseRR.GetOrderRequestMessage(
                self.strategy_id, order.order_id
            )
            latest_order = self.mediator.get_order(get_order_req)

            if latest_order is not None:
                latest_order.order.id = order.id

                for leg in latest_order.order.legs:
                    for leg2 in order.legs:
                        if leg.cusip == leg2.cusip:
                            leg.id = leg2.id

                # Update the DB record
                create_order_req = baseRR.UpdateDatabaseOrderRequest(latest_order.order)
                self.mediator.update_db_order(create_order_req)

                # If the Order's status is still open, update our flag
                if latest_order.order.isActive():
                    current_orders.append(latest_order.order)

        return current_orders

    ####################
    ### Option Chain ###
    ####################
    def build_option_chain_request(
        self, min_date, max_date
    ) -> baseRR.GetOptionChainRequestMessage:
        """Builds the option chain request message.

        Returns:
            baseRR.GetOptionChainRequestMessage: Option chain request message
        """
        return baseRR.GetOptionChainRequestMessage(
            self.strategy_id,
            contracttype=self.put_or_call,
            fromdate=min_date,
            todate=max_date,
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
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
        buying_power: float,
        liquidation_value: float,
        days_to_expiration: int,
        underlying_last_price: float,
        iv: float,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""

        logger.debug("get_best_strike")

        # Set Variables
        best_premium = float(0)
        best_strike = None

        # Calculate Risk Free Rate
        risk_free_rate = helpers.get_risk_free_rate()

        # Iterate through strikes
        for strike, details in strikes.items():
            # Sell @ Bid, Buy @ Ask
            option_price = details.bid if self.buy_or_sell == "SELL" else details.ask

            # Calculate Delta
            if self.use_vollib_for_greeks:
                calculated_delta = helpers.calculate_delta(
                    underlying_last_price,
                    strike,
                    risk_free_rate,
                    days_to_expiration,
                    self.put_or_call,
                    None,
                    option_price,
                )
            else:
                calculated_delta = details.delta

            # Make sure strike delta is less then our target delta
            if (abs(calculated_delta) <= abs(self.target_delta)) and (
                abs(calculated_delta) >= abs(self.min_delta)
            ):
                # Calculate the total premium for the strike based on our buying power
                qty = self.calculate_order_quantity(
                    strike, buying_power, liquidation_value
                )
                total_premium = option_price * qty

                # If the strike's premium is larger than our best premium, update it
                if total_premium > best_premium:
                    best_premium = total_premium
                    best_strike = details

        # Return the strike with the highest premium
        return best_strike

    def get_offsetting_strike(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_offsetting_strike")
        # Set Variables
        max_strike = strikes[0].strike
        best_strike = strikes[0]

        # Iterate through strikes, select the largest strike with a minimum ask price over 0
        for strike, details in strikes.items():
            if 0 < details.ask < best_strike.ask or (
                details.ask == best_strike.ask and strike > max_strike
            ):
                max_strike = strike
                best_strike = details

        # Return the strike with the highest premium
        return best_strike

    ####################
    ### Market Hours ###
    ####################
    def get_market_hours(
        self, date: dt.datetime
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        # Build Request
        request = baseRR.GetMarketHoursRequestMessage(
            self.strategy_id, market="OPTION", product="IND", datetime=date
        )

        # Get Market Hours
        return self.mediator.get_market_hours(request)

    def get_next_market_hours(
        self,
        date: dt.datetime = dt.datetime.now().astimezone(dt.timezone.utc),
    ) -> Union[baseRR.GetMarketHoursResponseMessage, None]:
        hours = self.get_market_hours(date)

        if hours is None or hours.end < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.get_next_market_hours(date + dt.timedelta(days=1))

        return hours

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
        helpers.send_notification(
            message, self.strategy_name, self.strategy_id, self.mediator
        )

    ###################
    ### Calculators ###
    ###################
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
