import datetime as dt
import logging
import logging.config
import math
import re
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
    profit_target_percent: Union[float, tuple] = attr.ib(default=0.7)
    max_loss_calc_percent: Union[float, dict[int, float]] = attr.ib(default=0.2)
    opening_order_loop_seconds: int = attr.ib(
        default=20, validator=attr.validators.instance_of(int)
    )
    sleep_until: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
    )
    early_market_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=15),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    late_market_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    after_hours_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
    )
    use_vollib_for_greeks: bool = attr.ib(
        default=True, validator=attr.validators.instance_of(bool)
    )
    offset_sold_positions: bool = attr.ib(
        default=False, validator=attr.validators.instance_of(bool)
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
        market_hours = self.get_next_market_hours()

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

    ###############################
    ### Closed Market Functions ###
    ###############################
    def process_closed_market(self, market_open: dt.datetime):
        # Sleep until market opens
        self.sleep_until_market_open(market_open)

    ############################
    ### Pre-Market Functions ###
    ############################
    def process_pre_market(self, market_open: dt.datetime):
        # Sleep until market opens
        self.sleep_until_market_open(market_open)

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
            f"Strategy {self.strategy_name} Has {'' if has_open_orders else 'No '}Open Order(s)"
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
            f"Strategy {self.strategy_name} Has {'' if has_open_orders else 'No '}Open Order(s)"
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
                    self.place_offsetting_order_loop(order)

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

    ######################
    ### Order Builders ###
    ######################
    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        account = self.mediator.get_account(
            baseRR.GetAccountRequestMessage(self.strategy_id, False, False)
        )

        if account is None:
            logger.error("Failed to get Account")
            return None

        # Get our available BP
        availbp = self.calculate_strategy_buying_power(
            account.currentbalances.buyingpower,
            account.currentbalances.liquidationvalue,
        )

        # Get default option chain
        chainrequest = self.build_option_chain_request()

        chain = self.mediator.get_option_chain(chainrequest)

        if chain is None or chain.status == "FAILED":
            logger.error("Failed to get Option Chain.")
            return None

        # Find next expiration
        expiration = self.get_next_expiration(chain)

        # If no valid expirations, exit.
        if expiration is None:
            return None

        # Find best strike to trade
        strike, quantity = self.get_best_strike_and_quantity(
            expiration.strikes,
            availbp,
            account.currentbalances.liquidationvalue,
            expiration.daystoexpiration,
            chain.underlyinglastprice,
        )

        # If no valid strikes, exit.
        if strike is None:
            return None

        offset_strike, offset_qty = self.get_offset_strike_and_quantity(
            account, expiration, strike, quantity
        )

        # Return Order
        return self.build_opening_order_request(
            strike, quantity, offset_strike, offset_qty
        )

    def build_offsetting_order(
        self, order: baseModels.Order
    ) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building Offsetting Order Request Messages"""
        logger.debug("build_offsetting_order")

        # Get option chain
        chainrequest = self.build_option_chain_request(dt.date.today(), dt.date.today())
        chain = self.mediator.get_option_chain(chainrequest)

        if chain is None or chain.status == "FAILED":
            logger.error("Failed to get Option Chain.")
            return None

        # Find next expiration
        if self.put_or_call == "CALL":
            expiration = chain.callexpdatemap[0]
        else:
            expiration = chain.putexpdatemap[0]

        # Get account balance
        account = self.mediator.get_account(
            baseRR.GetAccountRequestMessage(self.strategy_id, False, True)
        )

        if account is None or not hasattr(account, "positions"):
            logger.error("Failed to get Account")
            return None

        # Get Short Strike
        short_strike = helpers.get_strike_from_symbol(order.legs[0].symbol)

        if short_strike is None:
            return None

        # Find best strike to trade
        strike = self.get_offsetting_strike(
            expiration.strikes, account, order.quantity, short_strike
        )

        if strike is None:
            logger.error("Failed to get Offsetting Strike.")
            return None

        # Return Order
        return self.build_opening_order_request(strike, order.quantity, offsetting=True)

    def build_closing_order(
        self, original_order: baseModels.Order
    ) -> Union[None, baseRR.PlaceOrderRequestMessage]:
        """Builds a closing order request message for a given position."""
        # Build base order
        order_request = self.build_base_order_request_message(is_closing=True)

        # Build and append new legs
        for leg in original_order.legs:
            instruction = self.get_closing_order_instruction(leg.instruction)

            if instruction is None:
                break

            # Get the Strike
            original_strike = helpers.get_strike_from_symbol(leg.symbol)

            if original_strike is None:
                break

            # Build the new leg and append it
            new_leg = self.build_leg(
                leg.symbol, leg.description, leg.quantity, instruction, opening=False
            )
            order_request.order.legs.append(new_leg)

        if original_strike is None:
            return None

        pt = self.calculate_profit_target(original_strike)

        if pt is None:
            return None

        # Set and format the closing price
        order_request.order.price = helpers.format_order_price(
            original_order.price * (1 - pt)
        )

        # Return request
        return order_request

    def build_opening_order_request(
        self,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        qty: int,
        offset_strike: Union[
            baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None
        ] = None,
        offset_qty: int = 0,
        offsetting: bool = False,
    ) -> Union[baseRR.PlaceOrderRequestMessage, None]:

        # If no valid qty, exit.
        if qty is None or qty <= 0:
            return None

        # Determine how many legs are in the order
        single_leg = offset_strike is None or offset_qty <= 0

        # Quantity will be the smallest quantity > 0
        order_qty = min(qty, offset_qty) if offset_qty > 0 else qty

        # Build base order request
        order_request = self.build_base_order_request_message(is_single=single_leg)

        # Build the first leg
        first_leg = self.build_leg(
            strike.symbol,
            strike.description,
            order_qty,
            "BUY" if offsetting else self.buy_or_sell,
            True,
        )
        # Append the leg
        order_request.order.legs.append(first_leg)

        # Calculate price
        price = (strike.bid + strike.ask) / 2

        # If we are building an offse...
        if not single_leg and offset_strike is not None:
            # Build the offset leg
            long_leg = self.build_leg(
                offset_strike.symbol, offset_strike.description, order_qty, "BUY", True
            )
            # Append the leg
            order_request.order.legs.append(long_leg)

            # Recalculate the price
            price = price - (offset_strike.bid + offset_strike.ask) / 2

        # Format the price
        order_request.order.price = helpers.format_order_price(price)

        # Return the request message
        return order_request

    def build_base_order_request_message(
        self, is_closing: bool = False, is_single: bool = True
    ) -> baseRR.PlaceOrderRequestMessage:
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.order = baseModels.Order()
        orderrequest.order.strategy_id = self.strategy_id
        orderrequest.order.order_strategy_type = "SINGLE"
        orderrequest.order.duration = "GOOD_TILL_CANCEL"

        if self.offset_sold_positions is False or is_single:
            orderrequest.order.order_type = "LIMIT"
        elif (
            is_closing
            and self.buy_or_sell == "SELL"
            or not is_closing
            and self.buy_or_sell != "SELL"
        ):
            orderrequest.order.order_type = "LIMIT"
        else:
            orderrequest.order.order_type = "NET_CREDIT"

        orderrequest.order.session = "NORMAL"
        orderrequest.order.legs = list[baseModels.OrderLeg]()

        return orderrequest

    def build_leg(
        self,
        symbol: str,
        description: str,
        quantity: int,
        buy_or_sell: str,
        opening: bool,
    ) -> baseModels.OrderLeg:
        leg = baseModels.OrderLeg()
        leg.symbol = symbol
        leg.description = description
        leg.asset_type = "OPTION"
        leg.quantity = quantity
        leg.position_effect = "OPENING" if opening else "CLOSING"

        # Determine Instructions
        if buy_or_sell == "SELL" and opening:
            instruction = "SELL_TO_OPEN"
        elif buy_or_sell == "BUY" and opening:
            instruction = "BUY_TO_OPEN"
        elif buy_or_sell == "BUY":
            instruction = "BUY_TO_CLOSE"
        else:
            instruction = "SELL_TO_CLOSE"

        leg.instruction = instruction

        if leg.description is not None:
            match = re.search(r"([A-Z]{1}[a-z]{2} \d{1,2} \d{4})", leg.description)
            if match is not None:
                re_date = dt.datetime.strptime(match.group(), "%b %d %Y")
                leg.expiration_date = re_date.date()

        return leg

    #####################
    ### Order Placers ###
    #####################
    def cancel_order(self, order_id: int):
        # Build Request
        cancelorderrequest = baseRR.CancelOrderRequestMessage(
            self.strategy_id, order_id
        )

        # Send Request
        self.mediator.cancel_order(cancelorderrequest)

    def place_offsetting_order_loop(self, order: baseModels.Order) -> None:
        # Build Order
        offsetting_order_request = self.build_offsetting_order(order)

        # If neworder is None, exit.
        if offsetting_order_request is None:
            return

        # Place the order and if we have a result, return
        if self.place_order(offsetting_order_request):
            return

        # Otherwise, try again
        self.place_offsetting_order_loop(order)

    def place_new_orders_loop(self) -> None:
        """Looping Logic for placing new orders"""
        # Build Order
        new_order_request = self.build_new_order()

        # If neworder is None, exit.
        if new_order_request is None:
            return

        # Place the order and if we get a result, build the closing order.
        if self.place_order(new_order_request):
            closing_order = self.build_closing_order(new_order_request.order)
            if closing_order is not None:
                self.place_order(closing_order)
            return

        # Otherwise, try again
        self.place_new_orders_loop()

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
            self.cancel_order(int(new_order_result.order_id))

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

            if latest_order is None:
                continue

            latest_order.order.id = order.id

            for leg in latest_order.order.legs:
                for leg2 in order.legs:
                    if leg.cusip == leg2.cusip:
                        leg.id = leg2.id
                        break

            # Update the DB record
            create_order_req = baseRR.UpdateDatabaseOrderRequest(latest_order.order)
            self.mediator.update_db_order(create_order_req)

            # If the Order's status is still open, update our flag
            if latest_order.order.isActive():
                current_orders.append(latest_order.order)

        return current_orders

    def get_current_offsets(
        self, expiration: dt.date
    ) -> Union[list[baseModels.OrderLeg], None]:
        """Returns the first offsetting leg found in the DB for the given expiration date.

        Args:
            expiration (dt.date): Expiration date to search

        Returns:
            Union[baseModels.OrderLeg,None]: The leg from the DB, if found.
        """
        if expiration is None:
            raise RuntimeError("No Expiration Date Provided for Offset Lookup")

        # Read DB Orders
        open_offset_request = baseRR.ReadOffsetLegsByExpirationRequest(
            self.strategy_id,
            self.put_or_call,
            dt.datetime.combine(expiration, dt.time(0, 0)),
        )
        open_offsets = self.mediator.read_offset_legs_by_expiration(open_offset_request)

        if open_offsets is None or open_offsets.offset_legs == []:
            logger.info("No open offset exist.")
            return None

        return open_offsets.offset_legs

    def get_closing_order_instruction(
        self, opening_instruction: str
    ) -> Union[str, None]:
        """Returns the correct instruction for a closing order leg, based on the opening leg's instruction

        Args:
            opening_instruction (str): Instruction of the opening order's leg

        Returns:
            Union[str, None]: The closing instruction, or None if we shouldn't close this leg.
        """

        # Return the opposite instruction, if the leg matches our strategy
        if opening_instruction == "SELL_TO_OPEN" and self.buy_or_sell == "SELL":
            return "BUY"
        elif opening_instruction == "BUY_TO_OPEN" and self.buy_or_sell == "BUY":
            return "SELL"
        # If it doesn't match, return nothing, because we don't close offsetting legs, let them expire.
        else:
            return None

    def get_max_loss_percentage(self, dte) -> Union[float, None]:
        if isinstance(self.max_loss_calc_percent, float):
            return self.max_loss_calc_percent
        elif isinstance(self.max_loss_calc_percent, dict):
            return float(
                self.max_loss_calc_percent.get(dte)
                or self.max_loss_calc_percent[
                    min(
                        self.max_loss_calc_percent.keys(),
                        key=lambda key: abs(key - dte),
                    )
                ]
            )
        else:
            return None

    ####################
    ### Option Chain ###
    ####################
    def build_option_chain_request(
        self,
        min_date: Union[dt.date, None] = None,
        max_date: Union[dt.date, None] = None,
    ) -> baseRR.GetOptionChainRequestMessage:
        """Builds the option chain request message.

        Returns:
            baseRR.GetOptionChainRequestMessage: Option chain request message
        """
        if min_date is None:
            min_date = dt.date.today() + dt.timedelta(days=self.minimum_dte)

        if max_date is None:
            max_date = dt.date.today() + dt.timedelta(days=self.maximum_dte)

        return baseRR.GetOptionChainRequestMessage(
            self.strategy_id,
            contracttype=self.put_or_call,
            fromdate=min_date,
            todate=max_date,
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
        )

    def get_next_expiration(
        self,
        chain: baseRR.GetOptionChainResponseMessage,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate, None]:
        """Checks an option chain response for the next expiration date."""
        logger.debug("get_next_expiration")

        # Determine which expiration map to use
        if self.put_or_call == "CALL":
            expirations = chain.callexpdatemap

        elif self.put_or_call == "PUT":
            expirations = chain.putexpdatemap

        if expirations == []:
            logger.exception("Chain has no expirations.")
            return None

        # Initialize min DTE to infinity
        mindte = math.inf

        # Loop through expirations and find the minimum DTE
        expiration: baseRR.GetOptionChainResponseMessage.ExpirationDate
        for expiration in expirations:
            dte = expiration.daystoexpiration
            if dte < mindte:
                mindte = dte
                minexpiration = expiration

        # Return the min expiration
        return minexpiration

    def get_best_strike_and_quantity(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
        buying_power: float,
        liquidation_value: float,
        days_to_expiration: int,
        underlying_last_price: float,
    ) -> tuple:
        """Searches an option chain for the optimal strike."""

        logger.debug("get_best_strike")

        # Set Variables
        best_strike = None
        best_premium = float(0)
        best_quantity = 0

        # Calculate Risk Free Rate
        risk_free_rate = helpers.get_risk_free_rate()

        # Iterate through strikes
        for strike, detail in strikes.items():
            # Sell @ Bid, Buy @ Ask
            option_mid_price = (detail.bid + detail.ask) / 2

            # Calculate Delta
            if self.use_vollib_for_greeks:
                calculated_delta = helpers.calculate_delta(
                    underlying_last_price,
                    strike,
                    risk_free_rate,
                    days_to_expiration,
                    self.put_or_call,
                    None,
                    option_mid_price,
                )
            else:
                calculated_delta = detail.delta

            # Make sure strike delta is less then our target delta
            if abs(self.min_delta) <= abs(calculated_delta) <= abs(self.target_delta):
                # Calculate the total premium for the strike based on our buying power
                qty = self.calculate_order_quantity(
                    strike, buying_power, liquidation_value, days_to_expiration
                )
                total_premium = option_mid_price * qty

                # If the strike's premium is larger than our best premium, update it
                if total_premium > best_premium:
                    best_premium = total_premium
                    best_strike = detail
                    best_quantity = qty

        # Return the strike with the highest premium
        return best_strike, best_quantity

    def get_offset_strike_and_quantity(
        self,
        account: baseRR.GetAccountResponseMessage,
        expiration: baseRR.GetOptionChainResponseMessage.ExpirationDate,
        strike: baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike,
        quantity: int,
    ) -> tuple:
        # If we should immediately offset positions, decide how many we need.
        if not self.offset_sold_positions:
            return None, 0

        offset_qty = self.calculate_offset_leg_quantity(
            quantity, expiration.expirationdate
        )

        if offset_qty <= 0:
            return None, 0

        offset_strike = self.get_offsetting_strike(
            expiration.strikes, account, offset_qty, strike.strike
        )

        # If we should have an offset, but don't find one, exit.
        if offset_strike is None:
            logger.error("No offset strike found when expected.")
            raise RuntimeError("No offset strike found when expected.")

        return offset_strike, offset_qty

    def get_offsetting_strike(
        self,
        strikes: dict[
            float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike
        ],
        account: baseRR.GetAccountResponseMessage,
        quantity: int,
        short_strike: float,
    ) -> Union[baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike, None]:
        """Searches an option chain for the optimal strike."""
        logger.debug("get_offsetting_strike")

        if self.buy_or_sell == "BUY":
            logger.error("Cannot buy a max-width spread.")
            return None

        # Get Buying Power
        buying_power = self.calculate_strategy_buying_power(
            account.currentbalances.buyingpower,
            account.currentbalances.liquidationvalue,
        )

        # Determine max spread for the available buying power.
        max_strike_width = buying_power / 100 / quantity

        # Initialize values
        best_mid = float("inf")
        best_strike = 0.0

        for strike, detail in strikes.items():
            # Calc mid-price
            mid = (detail.bid + detail.ask) / 2

            # Determine if our strike fits the parameters
            good_strike_width = max_strike_width <= abs(short_strike - best_strike)
            good_strike_position = (
                (best_strike < strike)
                if (self.put_or_call == "PUT")
                else (best_strike > strike)
            )
            good_strike = (0.00 < mid < best_mid) or (
                (mid == best_mid) and good_strike_position and good_strike_width
            )

            # If the mid-price is lower, use it
            # If we're selling a PUT and the mid price is the same, but the strike is higher, use it.
            # If we're selling a CALL and the mid price is the same, but the strike is lower, use it.
            if good_strike:
                logger.info(
                    f"Risk: {(abs(strike-best_strike)*detail.multiplier)}, Buying Power: {buying_power}"
                )
                best_strike = strike
                best_mid = mid

        # Return the strike
        return strikes[best_strike]

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
        """Returns the Market Hours for the next working session

        Args:
            date (dt.datetime, optional): Date to start checking the market hours from. Defaults to dt.datetime.now().astimezone(dt.timezone.utc).

        Returns:
            Union[baseRR.GetMarketHoursResponseMessage, None]: Market Hours of the next working session
        """
        # Get the market hours
        hours = self.get_market_hours(date)

        # Variable for current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # If no hours were returned or the market is already closed for that day, search the next day.
        if hours is None or hours.end < now:
            return self.get_next_market_hours(date + dt.timedelta(days=1))

        # Return the market hours
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
    def calculate_profit_target(self, strike_price: float) -> Union[None, float]:
        """Calculates the profit target for the strategy based on the provided profit_target_percent in float or tuple

        Args:
            strike_price (float): Strike price to calculate the profit target against

        Returns:
            Union[None, float]: Profit target formatted as a float
        """
        # If it is a float, use the entered value
        if isinstance(self.profit_target_percent, float):
            if self.profit_target_percent == 1.0:
                return None
            return float(self.profit_target_percent)

        # If it is a tuple parse it as 1) Base PT, 2) %OTM Limit 3) Alternate PT
        elif isinstance(self.profit_target_percent, tuple):
            # Get current ticker price
            get_quote_request = baseRR.GetQuoteRequestMessage(
                self.strategy_id, [self.underlying]
            )
            current_quote = self.mediator.get_quote(get_quote_request)

            if current_quote is None:
                return None

            current_price = current_quote.instruments[0].lastPrice

            # Calculate opening position %OTM
            percent_otm = abs((current_price - strike_price) / current_price)

            # Determine profit target %
            if percent_otm < float(self.profit_target_percent[1]):
                pt = float(self.profit_target_percent[0])
            else:
                pt = float(self.profit_target_percent[2])

            logger.info(f"OTM: {percent_otm*100}%, PT: {pt*100}%")

            return pt

    def calculate_strategy_buying_power(
        self, buying_power: float, liquidation_value: float
    ) -> float:
        """Calculates the actual buying power based on the MaxLossCalcPercentage and current account balances.

        Args:
            buying_power (float): Actual account buying power
            liquidation_value (float): Actual account liquidation value

        Returns:
            float: Maximum buying power for this strategy
        """
        # Calculate how much this strategy could use, at most
        return liquidation_value * self.portfolio_allocation_percent

        # Return the smaller value of our actual buying power and calculated maximum buying power
        # return min(allocation_bp, buying_power)

    def calculate_order_quantity(
        self, strike: float, buying_power: float, liquidation_value: float, dte: int = 2
    ) -> int:
        """Calculates the number of positions to open for a given account and strike."""
        logger.debug("calculate_order_quantity")

        max_loss_percent = self.get_max_loss_percentage(dte)

        if max_loss_percent is None:
            return 0

        max_loss = strike * 100 * max_loss_percent

        # Calculate max buying power to use
        balance_to_risk = self.calculate_strategy_buying_power(
            buying_power, liquidation_value
        )

        # Return quantity
        return int(balance_to_risk // max_loss)

    def calculate_offset_leg_quantity(
        self, target_qty: int, expiration_date: dt.date
    ) -> int:
        """Calculates the quantity for an offset leg based on what has already been purchased for the given expiration.

        Args:
            target_qty (int): How many positions we need to offset
            expiration_date (dt.date): The date we need to offset on

        Returns:
            int: Quantity of offset legs needed.
        """
        # Get all offsetting legs on the date provided
        long_offsets = self.get_current_offsets(expiration_date)

        # If we don't have any, return the full amount
        if long_offsets is None:
            return target_qty

        # If we do have offsets, sum up the quantity
        open_offset_qty = sum(leg.quantity for leg in long_offsets)

        # Get working, closing orders to determine how many positions are accounted for
        req = baseRR.ReadOpenDatabaseOrdersRequest(strategy_id=self.strategy_id)
        open_orders = self.mediator.read_active_orders(req)

        # If we don't have any open orders, return either the difference between our target qty and open offset qty, or 0, whichever is larger
        if open_orders is None:
            return max(target_qty - open_offset_qty, 0)

        for order in open_orders.orders:
            for leg in order.legs:
                if (
                    leg.position_effect == "CLOSING"
                    and leg.put_call == self.put_or_call
                ):
                    open_offset_qty -= leg.quantity

        # Return either the difference between our target qty and actual qty, or 0, whichever is larger
        return max(target_qty - open_offset_qty, 0)
