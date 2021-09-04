import datetime as dt
import logging
import logging.config
import math
import time

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Component.abstractComponent import Component
from basetypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True, eq=False, repr=False)
class LongSharesStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for maintaining a Long Share Position as a percentage of liquid value."""

    strategy_name: str = attr.ib(
        default="VGSH Strategy", validator=attr.validators.instance_of(str)
    )
    underlying: str = attr.ib(
        default="VGSH", validator=attr.validators.instance_of(str)
    )
    portfolio_allocation_percent: float = attr.ib(
        default=0.90, validator=attr.validators.instance_of(float)
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

    # Core Strategy Process
    def process_strategy(self):
        """Main entry point to the strategy."""
        logger.debug("processstrategy")

        # Get current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # Check if should be sleeping
        if now < self.sleep_until:
            logger.debug("Markets Closed. Sleeping until {}".format(self.sleep_until))
            return

        # Check market hours
        hours = self.get_market_session_loop(now)

        if hours is None:
            logger.error("Failed to get market hours, exiting and retrying.")
            return

        # If the next market session is not today, wait for it
        if hours.start.day != now.day:
            self.go_to_sleep(now)

        # If Pre-Market
        if now < hours.start + dt.timedelta(minutes=self.minutes_after_open_delay):
            self.process_pre_market()

        # If In-Market
        elif (
            hours.start + dt.timedelta(minutes=self.minutes_after_open_delay)
            < now
            < hours.end
        ):
            self.process_open_market(now)

        # If After-Hours
        elif hours.end < now:
            self.process_after_hours(now)

    # Process Market
    def process_pre_market(self):
        """Pre-Market Trading Logic"""
        logger.debug("Processing Pre-Market.")

        self.go_to_sleep(dt.datetime.now())

    def process_open_market(self, now: dt.datetime):
        """Open Market Trading Logic"""
        logger.debug("Processing Open-Market")

        # Check Current position and account size
        request = baseRR.GetAccountRequestMessage(self.strategy_name, False, True)
        account = self.mediator.get_account(request)

        if account is None:
            logger.error("Failed to get account.")
            return

        # Get Share Price
        quoteRequest = baseRR.GetQuoteRequestMessage(
            self.strategy_name, [self.underlying]
        )
        share_price = self.mediator.get_quote(quoteRequest)

        if (
            share_price is None
            or share_price.instruments is None
            or share_price.instruments == []
        ):
            logger.error("Failed to get quote for {}.".format(self.underlying))
            return

        # Find Current Share Holding
        current_position = 0
        for position in account.positions:
            if position.symbol == self.underlying:
                current_position = position.longquantity
                break

        # Calculate share delta, rounded to 100
        target_value = (
            self.portfolio_allocation_percent * account.currentbalances.liquidationvalue
        )
        target_shares = int(target_value // share_price.instruments[0].lastPrice)
        rounded_target_shares = (target_shares // 100) * 100
        share_delta = current_position - rounded_target_shares

        # Log Status
        if share_delta == 0:
            logger.info(
                "Share Target: {} = Current Shares: {}. No change.".format(
                    rounded_target_shares, current_position
                )
            )
            self.go_to_sleep(now + dt.timedelta(days=1))
            return
        logger.info(
            "Share Target: {} <> Current Shares: {}. Placing Order...".format(
                rounded_target_shares, current_position
            )
        )

        # Place Order
        order = self.build_order(share_delta)

        # Confirm Order success and sleep until tomorrow
        result = self.place_order(order)

        # If successful, sleep until tomorrow
        if result:
            self.go_to_sleep(now + dt.timedelta(days=1))
        # If not, exit try again next time
        else:
            return

    def process_after_hours(self, now: dt.datetime):
        """After-Hours Trading Logic"""
        logger.debug("Processing After-Hours")

        self.go_to_sleep(now)

    def build_order(self, share_delta):
        order = baseRR.PlaceOrderRequestMessage()
        order.strategy_name = self.strategy_name
        order.ordertype = "MARKET"
        order.orderstrategytype = "SINGLE"
        order.ordersession = "NORMAL"
        order.duration = "DAY"
        order.price = None

        leg = baseRR.PlaceOrderRequestMessage.Leg()
        leg.instruction = "Buy" if share_delta < 0 else "Sell"
        leg.assettype = "EQUITY"
        leg.quantity = abs(share_delta)
        leg.symbol = self.underlying

        order.legs = []
        order.legs.append(leg)
        return order

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

        # Wait to let the Order process
        time.sleep(self.opening_order_loop_seconds)

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
                    int(leg.quantity),
                    True,
                    db_order_response.order_id,
                    0,
                )
                self.mediator.create_db_position(db_position_request)

        # Send a notification
        message = "Sold:<code>"

        for leg in orderrequest.legs:
            price = (
                "Market"
                if orderrequest.price is None
                else "{:,.2f}".format(orderrequest.price)
            )
            message += "\r\n - {}x {} @ ${}".format(
                str(leg.quantity), str(leg.symbol), price
            )

        message += "</code>"

        notification = baseRR.SendNotificationRequestMessage(message)

        self.mediator.send_notification(notification)

        # If we got here, return success
        return True

    @staticmethod
    def truncate(number: float, digits: int) -> float:
        """Truncates a float to a specified number of digits."""
        logger.debug("truncate")
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper

    def get_market_session_loop(
        self, date: dt.datetime
    ) -> baseRR.GetMarketHoursResponseMessage:
        """Looping Logic for getting the next open session start and end times"""

        logger.debug("get_market_session_loop")

        request = baseRR.GetMarketHoursRequestMessage(
            self.strategy_name, market="OPTION", product="EQO", datetime=date
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

    def go_to_sleep(self, start_date: dt.datetime):
        # Get Next Open
        nextmarketsession = self.get_market_session_loop(start_date)

        # Set sleepuntil
        self.sleep_until = (
            nextmarketsession.start
            + dt.timedelta(minutes=self.minutes_after_open_delay)
            - dt.timedelta(minutes=5)
        )

        logger.info(
            "Markets are closed until {}. Sleeping until {}".format(
                nextmarketsession.start
                + dt.timedelta(minutes=self.minutes_after_open_delay),
                self.sleep_until,
            )
        )
