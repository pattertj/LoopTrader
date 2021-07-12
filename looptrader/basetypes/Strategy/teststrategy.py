import datetime as dt
import logging
import logging.config
import time

import attr
import basetypes.Strategy.helpers as helpers
from basetypes.Component.abstractComponent import Component
from basetypes.Mediator.reqRespTypes import DatabaseOrder, DatabasePosition
from basetypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True, eq=False, repr=False)
class TestStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for trading Single Options by Delta."""

    strategy_name: str = attr.ib(
        default="Sample Strategy", validator=attr.validators.instance_of(str)
    )
    underlying: str = attr.ib(
        default="$SPX.X", validator=attr.validators.instance_of(str)
    )
    sleep_until: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
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
    portfolio_allocation: float = attr.ib(
        default=1.0, validator=attr.validators.instance_of(float)
    )
    buy_or_sell: str = attr.ib(
        default="SELL", validator=attr.validators.in_(["SELL", "BUY"])
    )
    put_or_call: str = attr.ib(
        default="PUT", validator=attr.validators.in_(["PUT", "CALL"])
    )
    max_delta: float = attr.ib(
        default=-0.07, validator=attr.validators.instance_of(float)
    )
    min_delta: float = attr.ib(
        default=-0.03, validator=attr.validators.instance_of(float)
    )
    min_dte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    max_dte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    profit_target: float = attr.ib(
        default=0.7, validator=attr.validators.instance_of(float)
    )
    max_loss_percent: float = attr.ib(
        default=0.2, validator=attr.validators.instance_of(float)
    )
    order_looping_in_seconds: int = attr.ib(
        default=10, validator=attr.validators.instance_of(int)
    )
    round_price_to: float = attr.ib(
        default=0.05, validator=attr.validators.instance_of(float)
    )
    risk_free_rate: float = attr.ib(
        default=0.05, init=False, validator=attr.validators.instance_of(float)
    )

    ####################
    ### Core Process ###
    ####################

    # Core Strategy Process
    def process_strategy(self):
        """Main entry point to the strategy."""
        # Now
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # Check if we should be sleeping
        if now < self.sleep_until:
            return

        # Get Market Hours
        market = helpers.get_next_market_hours(
            mediator=self.mediator, date=now, strategy_name=self.strategy_name
        )

        # Calculate Market Boundaries
        core_market_open = market.open + self.early_market_offset
        core_market_close = market.close - self.late_market_offset
        early_after_hours_close = market.close + self.after_hours_offset

        # If the next market open is not today, go to sleep until 15 minutes before market open to allow pre-market logic a chance.
        if market.open.day != now.day:
            self.process_closed_market(market.open - dt.timedelta(minutes=15))
            return

        # Check where we are
        if now < market.open:
            # Process Pre-Market
            self.process_pre_market(core_market_open)
        elif market.open < now < core_market_open:
            # Process Early Open Market
            self.process_early_open_market()
        elif core_market_open < now < core_market_close:
            # Process Core Open Market
            self.process_core_open_market()
        elif core_market_close < now < market.close:
            # Process Late Open Market
            self.process_late_open_market()
        elif market.close < now < early_after_hours_close:
            # Process After-Hours
            self.process_early_after_hours()
        elif early_after_hours_close < now:
            # Process After-Hours
            self.process_late_after_hours()

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
    def process_early_open_market(self):
        # Nothing to do.
        pass

    #################################
    ### Core Open Hours Functions ###
    #################################
    def process_core_open_market(self):
        # Get Positions from DB
        positions = helpers.get_db_positions(self.mediator, self.strategy_id)

        # If None, open a position
        if positions is None or positions.positions == []:
            self.place_opening_order()
            return

        # Iterate positions
        for position in positions.positions:
            # Process Position
            self.process_open_position(position)

    def process_open_position(self, position: DatabasePosition):
        # Get Orders from DB
        orders = helpers.get_db_orders(self.mediator, position.position_id)

        # If none, check expiration
        if orders is None:
            self.process_position_expiration(position)
            return

        # If yes, call broker and process Orders by status
        order: DatabaseOrder
        for order in orders:
            if order.status == "CANCELLED":
                # Cancelled
                self.process_cancelled_order()
            elif order.status == "WORKING":
                # Working
                self.process_working_order()
            elif order.status == "CLOSED":
                # Closed
                self.process_closed_order(order)
            else:
                logger.error(
                    "Position {}, Order {}, has invalid Status {}.".format(
                        position.position_id, order.order_id, order.status
                    )
                )

    def process_cancelled_order(self):
        # Open new Closing Order
        self.place_closing_order()

    def process_working_order(self):
        # Nothing to do, continue
        pass

    def process_closed_order(self, order: DatabaseOrder):
        # Close Order in DB
        helpers.close_db_order(self.mediator, order.order_id)
        # TODO: Close Position in DB
        # helpers.close_db_position(self.mediator, order.position_id)

    def process_position_expiration(self, position):
        if position.expiration_date < dt.datetime.now().astimezone(dt.timezone.utc):
            # If expired, close Position in DB
            helpers.close_db_position(self.mediator, position.positionid)
            # Open a new Position
            self.place_opening_order()
            return

        # If not, open new Closing Order
        self.place_closing_order()

    ########################
    ### Late Open Market ###
    ########################
    def process_late_open_market(self):
        # Get Positions from DB
        positions = helpers.get_db_positions(self.mediator, self.strategy_id)

        # If None, open a position
        if positions is None:
            self.place_opening_order()
            return

        # Iterate positions
        for position in positions:
            # Process Position after-hours
            self.process_late_open_market_position(position)

    def process_late_open_market_position(self, position):
        # Get Orders from DB
        orders = helpers.get_db_orders(self.mediator, position.positionid)

        # If none, do nothing
        if orders is None:
            return

        # Cancel closing Orders with Broker
        for order in orders:
            self.place_order_cancel(order)

    #############################
    ### After-Hours Functions ###
    #############################
    def process_early_after_hours(self):
        # Get Positions
        positions = helpers.get_db_positions(self.mediator, self.strategy_id)

        if positions is None:
            logger.info("No Positions Found")
            return

        # Iterate Positions and get orders
        for position in positions:
            orders = helpers.get_db_orders(self.mediator, position.positionid)

            # Check if a closing Order exists
            closing_order_exists = any(
                order.status == "QUEUED"
                and order.legs[0].symbol == self.symbol
                and order.legs[0].instruction == "BUY_TO_CLOSE"
                for order in orders
            )

            # If no closing Order, place one
            if not closing_order_exists:
                self.place_closing_order(position)

    def process_late_after_hours(self):
        # Find next market open
        hours = self.find_next_market_hours()

        # Sleep until market opens
        self.sleep_until_market_open(hours.open)

    ########################
    ### Shared Functions ###
    ########################
    def sleep_until_market_open(self, datetime: dt.datetime):
        # Populate sleep-until variable
        self.sleep_until = datetime
        # Send a notification that we are sleeping
        helpers.send_notification(
            mediator=self.mediator,
            message="Markets are closed until {}. Sleeping until {}".format(
                datetime, self.sleep_until
            ),
        )

    #################################
    ### Order Placement Functions ###
    #################################
    def place_opening_order(self):
        # Build Order Request
        order_request = self.generate_opening_order_request()

        # Place Order
        new_order_response = helpers.place_order(order_request)

        # Process the order response message.
        self.process_opening_order_response(new_order_response)

    def generate_opening_order_request(self):
        # Get Option Chain
        option_chain = helpers.get_option_chain(
            self.mediator,
            self.strategy_name,
            self.put_or_call,
            self.min_dte,
            self.max_dte,
            self.underlying,
        )

        # Get Next Valid Expiration
        expiration = helpers.get_next_expiration(option_chain, self.put_or_call)

        # Calculate Deltas
        risk_free_rate = helpers.get_risk_free_rate()

        for strike in expiration.strikes.values():
            if strike.strike > option_chain.underlyinglastprice:
                iv = 1
            else:
                iv = helpers.calculate_iv(
                    (strike.bid + strike.ask) / 2,
                    option_chain.underlyinglastprice,
                    strike.strike,
                    risk_free_rate,
                    expiration.daystoexpiration,
                    self.put_or_call,
                )

            delta = helpers.calculate_delta(
                option_chain.underlyinglastprice,
                strike.strike,
                risk_free_rate,
                expiration.daystoexpiration,
                self.put_or_call,
                iv,
            )
            strike.delta = delta

        # Get Account Balance
        account = helpers.get_account(self.mediator, self.strategy_name, False, False)

        # If no Strike, exit
        if account is None or account.currentbalances is None:
            logger.error("Failed to return account balance.")
            return None

        # Calculate BP to use
        buying_power = (
            account.currentbalances.liquidationvalue * self.portfolio_allocation
        )

        # Find the max total premium where the delta is between our min and max delta.
        best_strike = helpers.get_best_strike_by_delta(
            expiration.strikes,
            self.min_delta,
            self.max_delta,
            buying_power,
            self.max_loss_percent,
        )

        # If no Strike, exit
        if best_strike is None:
            logger.error("Failed to find a valid strike.")
            return None

        # Return Single Order Request
        return helpers.build_single_order_request(
            best_strike[0],
            best_strike[1],
            best_strike[2],
            self.buy_or_sell,
            "OPEN",
            self.strategy_name,
        )

    def process_opening_order_response(self, new_order_response):
        # Wait configured time
        time.sleep(self.order_looping_in_seconds)

        # Check Order Status
        new_order = helpers.get_order(
            self.mediator, int(new_order_response.orderid), self.strategy_name
        )

        # If successful
        if new_order is not None and new_order.status != "FILLED":
            # Log Order in DB
            helpers.create_db_order(self.mediator, new_order.orderid, self.strategy_id)
            # Log Position in DB
            helpers.create_db_position(
                self.mediator,
                self.strategy_id,
                new_order.symbol,
                new_order.quantity,
                new_order.orderid,
            )
            # Send Notification
            helpers.send_notification()

        # If it failed
        else:
            # Cancel the Order
            helpers.cancel_broker_order(
                self.mediator, new_order.orderid, self.strategy_id
            )
            # Retry
            self.place_opening_order()

    def place_closing_order(self, position):
        # Build Request
        request = helpers.build_single_order_request(
            position.strike,
            position.quantity,
            position.price * self.profit_target,
            self.buy_or_sell,
            "OPEN",
            self.strategy_name,
        )

        # Place Order
        response = helpers.place_order(request)

        # Confirm Order
        closing_order = helpers.get_order(
            self.mediator, int(response.orderid), self.strategy_name
        )

        # Log Order in DB
        helpers.create_db_order(self.mediator, closing_order.orderid, self.strategy_id)

        # Send Notification
        helpers.send_notification()

    def place_order_cancel(self, order):
        # Build Request
        request = ""

        # Place Order
        cancel_response = helpers.cancel_broker_order(self.mediator, request)

        # Confirm Cancel was successful, or try again
        if cancel_response == "200:":
            cancel_status = helpers.get_order(order.order_id)
        else:
            return self.place_order_cancel(order)

        # If successful
        if cancel_status == "CANCELLED":
            # Log Order in DB
            helpers.cancel_db_order(self.mediator, order.orderid)
            # Send Notification
            helpers.send_notification("")
            return

        # If it failed, log error, send notification, exit
        message = "Failed to Cancel Order {}".format(order)
        logger.error(message)
        helpers.send_notification(self.mediator, message)


# CREATE TABLE trades (id INTEGER PRIMARY KEY,status INTEGER,entry_order_id INTEGER,exit_order_id INTEGER, target_delta REAL);
# CREATE TABLE orders (id INTEGER PRIMARY KEY,trade_id INTEGER,symbol TEXT,strike REAL,action INTEGER,time TEXT,size INTEGER,price REAL,commissions REAL,underlying_price REAL,delta REAL,implied_volatility REAL,vix REAL,expiry_date TEXT, usdcad REAL, right TEXT,FOREIGN KEY(trade_id) REFERENCES trades(id));
