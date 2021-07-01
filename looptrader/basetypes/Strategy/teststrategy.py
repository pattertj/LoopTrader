import datetime as dt
import logging
import logging.config

import attr

# import basetypes.Mediator.reqRespTypes as baseRR
import helpers
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
    sleepuntil: dt.datetime = attr.ib(
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
    early_after_hour_offset: dt.timedelta = attr.ib(
        default=dt.timedelta(minutes=5),
        validator=attr.validators.instance_of(dt.timedelta),
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
        if now < self.sleepuntil:
            return

        # Get Market Hours
        market = helpers.get_market_hours(self.mediator, now, self.strategy_name)

        # Calculate Market Boundaries
        core_market_open = market.open + self.early_market_offset
        core_market_close = market.close - self.late_market_offset
        early_after_hours_close = market.close + self.early_after_hour_offset

        # Check where we are
        if now < market.open:
            # Process Pre-Market
            self.process_pre_market()
        elif market.open < now < core_market_open:
            # Process Early Open Market
            self.process_early_open_market(now, market)
        elif core_market_open < now < core_market_close:
            # Process Core Open Market
            self.process_core_open_market(now, market)
        elif core_market_close < now < market.close:
            # Process Late Open Market
            self.process_late_open_market(now, market)
        elif market.close < now < early_after_hours_close:
            # Process After-Hours
            self.process_early_after_hours(now, market)
        elif early_after_hours_close < now:
            # Process After-Hours
            self.process_late_after_hours(now, market)

        return

    ############################
    ### Pre-Market Functions ###
    ############################
    def process_pre_market(self):
        # Sleep until market opens
        self.sleep_until_market_open()

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
        if positions is None:
            self.place_opening_order()
            return

        # Iterate positions
        for position in positions:
            # Process Position
            self.process_open_position(position)

    def process_open_position(self, position):
        # Get Orders from DB
        orders = helpers.get_db_orders(self.mediator, position.positionid)

        # If none, check expiration
        if orders is None:
            self.process_position_expiration(position)
            return

        # If yes, call broker and process Orders by status
        for order in orders:
            if order.status == "CANCELLED":
                # Cancelled
                self.process_cancelled_order()
            elif order.status == "WORKING":
                # Working
                self.process_working_order()
            elif order.status == "CLOSED":
                # Closed
                self.process_closed_order()
            else:
                logger.error(
                    "Position {}, Order {}, has invalid Status {}.".format(
                        position.id, order.id, order.status
                    )
                )

    def process_cancelled_order(self):
        # Open new Closing Order
        self.place_closing_order()

    def process_working_order(self):
        # Nothing to do, continue
        pass

    def process_closed_order(self, order):
        # Close Order in DB
        helpers.close_db_order(self.mediator, order.orderid)
        # Close Position in DB
        helpers.close_db_position(self.mediator, order.positionid)

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
        self.sleepuntil = datetime

    def find_next_market_hours(
        self, date: dt.datetime = dt.datetime.now().astimezone(dt.timezone.utc)
    ):
        hours = helpers.get_market_hours(self.mediator, date, self.strategy_name)

        if hours is None or hours.end + dt.timedelta(
            minutes=15
        ) < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.find_next_market_hours(date + dt.timedelta(days=1))

        return hours

    #################################
    ### Order Placement Functions ###
    #################################
    def place_opening_order(self):
        # Get Strike
        # Calculate Quantity
        # Calculate Price
        # Populate Order Fields
        # Place Order
        # Wait configured time
        # If successful
        #   Log Order in DB
        #   Log Position in DB
        #   Send Notification
        # If it failed
        #   Cancel the Order
        #   Retry
        pass

    def place_closing_order(self, position):
        # Calculate Close Price
        # Copy Details
        # Populate remaining Order fields
        # Place Order
        # Log Order in DB
        # Send Notification
        pass

    def place_order_cancel(self, order):
        # Build Request
        request = ""

        # Place Order
        response = helpers.cancel_broker_order(self.mediator, request)

        # If successful
        if response:
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
