import datetime as dt
import logging
import logging.config
import time
from dataclasses import dataclass
from typing import List

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@dataclass
class CspByDeltaStrategy(Strategy, Component):
    strategy_name: str = 'Sample Strategy'
    underlying: str = "$SPX.X"
    portfolioallocationpercent: float = 1.0
    buy_or_sell: str = 'Sell'
    targetdelta: float = .06
    minimumdte: int = 1
    maximumdte: int = 4
    profittargetpercent: float = .7
    maxlosscalcpercent: float = .2
    openingorderloopseconds: int = 10

    # Core Strategy Process
    def processstrategy(self) -> bool:
        # Check market hours
        request = baseRR.GetMarketHoursRequestMessage(markets={'OPTION'})
        hours = self.mediator.get_market_hours(request)

        # Get current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # If Pre-Market
        if now < hours.start:
            self.process_pre_market()

        # If In-Market
        elif hours.start < now < hours.end:
            self.process_open_market(hours, now)

        # If After-Hours
        elif hours.end < now:
            self.process_after_hours(hours, now)

    # Process Market Hours
    def process_pre_market(self):
        # Exit.
        print("Pre-market, nothing to do.")

    def process_open_market(self, hours: baseRR.GetMarketHoursResponseMessage, now: dt.datetime):
        minutestoclose = (hours.end - now).total_seconds() / 60
        print("Market Open")

        # Process Expiring Positions
        self.process_expiring_positions(minutestoclose)

        # Place New Orders
        self.place_new_orders_loop()

        # Process Closing Orders
        self.process_closing_orders(minutestoclose)

    def process_closing_orders(self, minutestoclose):
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
                    self.mediator.place_order(order)

    # Open Market Helpers
    def process_expiring_positions(self, minutestoclose):
        # If there is more then 15min to the close, don't do this.
        if minutestoclose > 15:
            return

        print("15min to close or less")

        # Open expiring positions should be off-set to free-up buying power
        offsettingorders = self.build_offsetting_orders()

        # Place new order loop
        for order in offsettingorders:
            self.place_order_loop(order)

    def build_offsetting_orders(self) -> List[baseRR.PlaceOrderRequestMessage]:
        # Read positions
        request = baseRR.GetAccountRequestMessage(False, True)
        account = self.mediator.get_account(request)

        # If not positions, nothing to offset
        if account.positions is None:
            return

        response = [baseRR.PlaceOrderResponseMessage]

        # Check for expiration today
        # for position in account.positions:
        # if position.expirationdate == now:
        # Check DB if it is our positions
        # If true, process it
        # Get today's option chain
        # Find a cheap option to offset
        # Build Order
        # Append to Reponse
        # response.append(offsetorder)

        # Once we have reviewed all postiions, exit.
        return response

    def process_after_hours(self, hours: baseRR.GetMarketHoursResponseMessage, now: dt.datetime):
        # Get the number of minutes since close
        minutesafterclose = (now - hours.end).total_seconds() / 60
        print("After-Hours")

        # If within 15min after close
        if minutesafterclose < 15:
            print("15min after close or less")
            # Build closing orders
            closingorders = self.build_closing_orders()

            # Place closing Orders
            if closingorders is not None:
                for order in closingorders:
                    self.mediator.place_order(order)

    # Helpers

    def place_new_orders_loop(self) -> None:
        # Build Order
        neworder = self.build_new_order()

        # If neworder is None, exit.
        if neworder is None:
            return

        # Try to place the Order
        neworderresult = self.mediator.place_order(neworder)

        # Wait to let the Order process
        time.sleep(self.openingorderloopseconds)

        # Re-get the Order
        getorderrequest = baseRR.GetOrderRequestMessage(neworderresult.orderid)
        processedorder = self.mediator.get_order(getorderrequest)

        # If the order isn't filled
        if processedorder.status != 'FILLED':
            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(neworderresult.orderid)
            self.mediator.cancel_order(cancelorderrequest)

            # Try again
            self.place_new_orders_loop()

        return

    def build_new_order(self) -> baseRR.PlaceOrderRequestMessage:
        # Get account balance
        # Calculate trade date
        # Get option chain
        # Find strike to trade
        # Check if we have enough buying power to sell 1 or more, exit if not
        # Calculate price
        # Build Order
        # Return Order
        pass

    def build_cancel_closing_orders(self) -> List[baseRR.CancelOrderRequestMessage]:
        pass

    def build_closing_orders(self) -> List[baseRR.PlaceOrderRequestMessage]:
        pass

    def place_order_loop(self) -> None:
        pass
