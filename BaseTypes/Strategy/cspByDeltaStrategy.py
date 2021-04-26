import datetime as dt
import logging
import logging.config
import math
import time
from typing import List

import attr
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@attr.s(auto_attribs=True)
class CspByDeltaStrategy(Strategy, Component):
    strategy_name: str = 'Sample Strategy'
    underlying: str = "$SPX.X"
    portfolioallocationpercent: float = attr.ib(default=1.0, validator=attr.validators.instance_of(float))
    buy_or_sell: str = attr.ib(default='SELL', validator=attr.validators.in_(['SELL', 'BUY']))
    targetdelta: float = attr.ib(default=-.06, validator=attr.validators.instance_of(float))
    mindelta: float = attr.ib(default=-.03, validator=attr.validators.instance_of(float))
    minimumdte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximumdte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    profittargetpercent: float = attr.ib(default=.7, validator=attr.validators.instance_of(float))
    maxlosscalcpercent: float = attr.ib(default=.2, validator=attr.validators.instance_of(float))
    openingorderloopseconds: int = attr.ib(default=10, validator=attr.validators.instance_of(int))

    # Core Strategy Process
    def processstrategy(self) -> bool:
        # Check market hours
        request = baseRR.GetMarketHoursRequestMessage(market='OPTION', product='IND')
        hours = self.mediator.get_market_hours(request)

        # Get current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # If Pre-Market
        if now < hours.start:
            self.process_pre_market()

        # If In-Market
        elif hours.start < now < hours.end:
            self.process_open_market(hours.end, now)

        # If After-Hours
        elif hours.end < now:
            self.process_after_hours(hours.end, now)

    # Process Market Hours
    def process_pre_market(self):
        # Exit.
        print("Pre-market, nothing to do.")

    def process_open_market(self, close: dt.datetime, now: dt.datetime):
        minutestoclose = (close - now).total_seconds() / 60
        print("Market Open")

        # Process Expiring Positions
        self.process_expiring_positions(minutestoclose)

        # Place New Orders
        self.place_new_orders_loop()

        # Process Closing Orders
        self.process_closing_orders(minutestoclose)

    def process_after_hours(self, close: dt.datetime, now: dt.datetime):
        # Get the number of minutes since close
        minutesafterclose = (now - close).total_seconds() / 60
        print("After-Hours")

        # If beyond 15 min after close, exit
        if minutesafterclose > 15:
            return

        print("15min after close or less")
        # Build closing orders
        closingorders = self.build_closing_orders()

        # Place closing Orders
        if closingorders is not None:
            for order in closingorders:
                self.mediator.place_order(order)

    # Open Market Helpers
    def process_expiring_positions(self, minutestoclose):
        # If there is more then 15min to the close, we can skip this logic.
        if minutestoclose > 15:
            return

        # Open expiring positions should be off-set to free-up buying power
        offsettingorders = self.build_offsetting_orders()

        # Place new order loop
        for order in offsettingorders:
            self.place_order_loop(order)

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

    def build_offsetting_orders(self) -> list[baseRR.PlaceOrderRequestMessage]:
        pass

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
        #         # Check DB if it is our positions
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

    # Order Builders
    def build_new_order(self) -> baseRR.PlaceOrderRequestMessage:
        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(False, False)
        account = self.mediator.get_account(accountrequest)

        # Calculate trade date
        startdate = (dt.date.today() + dt.timedelta(days=self.minimumdte))
        enddate = (dt.date.today() + dt.timedelta(days=self.maximumdte))

        # Get option chain
        chainrequest = baseRR.GetOptionChainRequestMessage(contracttype='PUT', fromdate=startdate, todate=enddate, symbol=self.underlying, includequotes=False, optionrange='OTM')

        chain = self.mediator.get_option_chain(chainrequest)

        # Find strike to trade
        expiration = self.get_next_expiration(chain.putexpdatemap)
        strike = self.get_best_strike(expiration.strikes, self.targetdelta, account.currentbalances.buyingpower)

        # If no valid strikes, exit.
        if strike is None:
            return None

        # Calculate Quantity
        qty = self.calculate_order_quantity(strike.strike, account.currentbalances.buyingpower)

        # Calculate price
        price = (strike.bid + strike.ask) / 2

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.price = price
        orderrequest.quantity = qty
        orderrequest.symbol = strike.symbol

        # Return Order
        return orderrequest

    def build_cancel_closing_orders(self) -> List[baseRR.CancelOrderRequestMessage]:
        pass

    def build_closing_orders(self) -> List[baseRR.PlaceOrderRequestMessage]:
        pass

    # Order Placers
    def place_new_orders_loop(self) -> None:
        # Build Order
        neworder = self.build_new_order()

        # If neworder is None, exit.
        if neworder is None:
            return

        # Place the order and check the result
        result = self.place_order_loop(neworder)

        # If successful, return
        if result:
            return

        # Otherwise, try again
        self.place_new_orders_loop()

        return

    def place_order_loop(self, orderrequest: baseRR.PlaceOrderRequestMessage) -> bool:
        # Try to place the Order
        neworderresult = self.mediator.place_order(orderrequest)

        # If closing order, let the order ride, otherwise continue logic
        if orderrequest.positioneffect == "CLOSING":
            return True

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

            # Return failure to fill order
            return False

        # If we got here, return success
        return True

    # Helpers
    def get_next_expiration(self, expirations: list[baseRR.GetOptionChainResponseMessage.ExpirationDate]) -> baseRR.GetOptionChainResponseMessage.ExpirationDate:
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

    def get_best_strike(self, strikes: dict[float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike], delta: float, buyingpower: float) -> baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike:
        # Set Variables
        bestpremium = float(0)
        beststrike = None

        # Iterate through strikes
        for strike, details in strikes.items():
            # Make sure strike delta is less then our target delta
            if (abs(details.delta) <= abs(self.targetdelta)) and (abs(details.delta) >= abs(self.mindelta)):
                # Calculate the total premium for the strike based on our buying power
                qty = self.calculate_order_quantity(strike, buyingpower)
                totalpremium = ((details.bid + details.ask) / 2) * qty

                # If the strike's premium is larger than our best premium, update it
                if totalpremium > bestpremium:
                    bestpremium = totalpremium
                    beststrike = details

        # Return the strike with the highest premium
        return beststrike

    def calculate_order_quantity(self, strike, buyingpower) -> int:
        # Calculate max loss per contract
        max_loss = strike * 100 * float(self.maxlosscalcpercent)

        # Calculate max buying power to use
        balance_to_risk = buyingpower * float(self.portfolioallocationpercent)

        # Calculate trade size
        trade_size = balance_to_risk // max_loss

        # Log Details
        logger.info("Max Loss: {}, Allocated Buying Power: {}, Trade Qty: {}".format(
            str(max_loss), str(balance_to_risk), str(trade_size)))

        # Return quantity
        return int(trade_size)
