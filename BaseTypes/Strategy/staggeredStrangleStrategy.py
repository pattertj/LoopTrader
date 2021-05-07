import datetime as dt
import logging
import logging.config
import math
import time

import attr
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@attr.s(auto_attribs=True)
class StaggeredStrangleStrategy(Strategy, Component):
    strategy_name: str = attr.ib(default="Sample Strategy", validator=attr.validators.instance_of(str))
    underlying: str = attr.ib(default="$SPX.X", validator=attr.validators.instance_of(str))
    portfolioallocationpercent: float = attr.ib(default=1.0, validator=attr.validators.instance_of(float))
    long_or_short: str = attr.ib(default='SHORT', validator=attr.validators.in_(['LONG', 'SHORT']))
    minimumdte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximumdte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    puttargetdelta: float = attr.ib(default=-.06, validator=attr.validators.instance_of(float))
    putmindelta: float = attr.ib(default=-.03, validator=attr.validators.instance_of(float))
    putprofittargetpercent: float = attr.ib(default=.7, validator=attr.validators.instance_of(float))
    putmaxlosscalcpercent: float = attr.ib(default=.2, validator=attr.validators.instance_of(float))
    calltargetdelta: float = attr.ib(default=-.02, validator=attr.validators.instance_of(float))
    callmindelta: float = attr.ib(default=-.01, validator=attr.validators.instance_of(float))
    callprofittargetpercent: float = attr.ib(default=.79, validator=attr.validators.instance_of(float))
    callmaxlosscalcpercent: float = attr.ib(default=.2, validator=attr.validators.instance_of(float))
    openingorderloopseconds: int = attr.ib(default=20, validator=attr.validators.instance_of(int))
    sleepuntil: dt.datetime = attr.ib(init=False, default=dt.datetime.now().astimezone(dt.timezone.utc), validator=attr.validators.instance_of(dt.datetime))
    minutesafteropendelay: int = attr.ib(default=3, validator=attr.validators.instance_of(int))

    # Core Strategy Process
    def processstrategy(self) -> bool:
        # Get current datetime
        now = dt.datetime.now().astimezone(dt.timezone.utc)

        # Check if should be sleeping
        if now < self.sleepuntil:
            logger.debug("Markets Closed. Sleeping until {}".format(self.sleepuntil))
            return

        # Check market hours
        request = baseRR.GetMarketHoursRequestMessage(market='OPTION', product='IND')
        hours = self.mediator.get_market_hours(request)

        if hours is None:
            logger.error("Failed to get market hours, exiting and retrying.")
            return

        # If Pre-Market
        if now < hours.start + dt.timedelta(minutes=self.minutesafteropendelay):
            self.process_pre_market()

        # If In-Market
        elif hours.start + dt.timedelta(minutes=self.minutesafteropendelay) < now < hours.end:
            self.process_open_market(hours.end, now)

        # If After-Hours
        elif hours.end < now:
            self.process_after_hours(hours.end, now)

    # Process Market Hours
    def process_pre_market(self):
        logger.debug("Processing Pre-Market.")

        # Get Next Open
        nextmarketsession = self.get_market_session_loop(dt.datetime.now())
        # Set sleepuntil
        self.sleepuntil = nextmarketsession.start + dt.timedelta(minutes=self.minutesafteropendelay) - dt.timedelta(minutes=5)

        logger.info("Markets are closed until {}. Sleeping until {}".format(nextmarketsession.start + dt.timedelta(minutes=self.minutesafteropendelay), self.sleepuntil))

        # Exit.
        return

    def process_open_market(self, close: dt.datetime, now: dt.datetime):
        logger.debug("Processing Open-Market")

        # Get the number of minutes till close
        minutestoclose = (close - now).total_seconds() / 60

        # Process Expiring Positions
        self.process_expiring_positions(minutestoclose)

        # Place New Orders
        self.place_new_orders_loop('PUT')
        self.place_new_orders_loop('CALL')

        # Process Closing Orders
        self.process_closing_orders(minutestoclose)

    def process_after_hours(self, close: dt.datetime, now: dt.datetime):
        logger.debug("Processing After-Hours")

        # Get the number of minutes since close
        minutesafterclose = (now - close).total_seconds() / 60

        # If beyond 5 min after close, exit
        if minutesafterclose > 5:
            # Get Next Open
            nextmarketsession = self.get_market_session_loop(dt.datetime.now() + dt.timedelta(days=1))
            # Set sleepuntil
            self.sleepuntil = nextmarketsession.start - dt.timedelta(minutes=5)

            logger.info("Markets are closed until {}. Sleeping until {}".format(nextmarketsession.start, self.sleepuntil))
            return

        # Build closing orders
        closingorders = self.build_closing_orders()

        # Place closing Orders
        if closingorders is not None:
            for order in closingorders:
                self.mediator.place_order(order)

        logger.info("Placed {} Closing Orders".format(len(closingorders)))

    # Open Market Helpers
    def process_expiring_positions(self, minutestoclose):
        logger.debug("process_expiring_positions")
        # If there is more then 15min to the close, we can skip this logic.
        if minutestoclose > 15:
            return

        # Open expiring positions should be off-set to free-up buying power
        offsettingorders = self.build_offsetting_orders()

        # Place new order loop
        if offsettingorders is not None:
            for order in offsettingorders:
                self.place_order_loop(order)

    def process_closing_orders(self, minutestoclose):
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
                    self.mediator.place_order(order)

    def build_offsetting_orders(self) -> list[baseRR.PlaceOrderRequestMessage]:
        logger.debug("build_offsetting_orders")
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
        #         # TODO: Check DB if it is our positions
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
    def build_new_order(self, putorcall: str) -> baseRR.PlaceOrderRequestMessage:
        logger.debug("build_new_order")

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(False, False)
        account = self.mediator.get_account(accountrequest)

        # Calculate trade date
        startdate = (dt.date.today() + dt.timedelta(days=self.minimumdte))
        enddate = (dt.date.today() + dt.timedelta(days=self.maximumdte))

        # Get option chain
        chainrequest = baseRR.GetOptionChainRequestMessage(contracttype=putorcall, fromdate=startdate, todate=enddate, symbol=self.underlying, includequotes=False, optionrange='OTM')

        chain = self.mediator.get_option_chain(chainrequest)

        # Should we even try?
        estbp = .9 * (chain.underlyinglastprice * .2 * 100)
        availbp = account.currentbalances.buyingpower

        if (estbp > availbp):
            return

        # Find strike to trade
        if putorcall == 'PUT':
            expdatemap = chain.putexpdatemap
        else:
            expdatemap = chain.callexpdatemap

        expiration = self.get_next_expiration(expdatemap)
        strike = self.get_best_strike(expiration.strikes, account.currentbalances.buyingpower, account.currentbalances.liquidationvalue, putorcall)

        # If no valid strikes, exit.
        if strike is None:
            return None

        # Calculate Quantity
        qty = self.calculate_order_quantity(strike.strike, account.currentbalances.buyingpower, account.currentbalances.liquidationvalue, putorcall)

        # Calculate price
        price = (strike.bid + strike.ask) / 2
        formattedprice = self.format_order_price(price)

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.orderstrategytype = 'SINGLE'
        orderrequest.assettype = 'OPTION'
        orderrequest.duration = 'GOOD_TILL_CANCEL'
        orderrequest.instruction = 'SELL_TO_OPEN'
        orderrequest.ordertype = 'LIMIT'
        orderrequest.ordersession = 'NORMAL'
        orderrequest.positioneffect = 'OPENING'
        orderrequest.price = formattedprice
        orderrequest.quantity = qty
        orderrequest.symbol = strike.symbol

        # Return Order
        return orderrequest

    def build_cancel_closing_orders(self) -> list[baseRR.CancelOrderRequestMessage]:
        logger.debug("build_cancel_closing_orders")

        orderrequests = []

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(True, False)
        account = self.mediator.get_account(accountrequest)

        # Look for open positions
        for order in account.orders:
            # TODO: If positions belongs to this strat...
            if order.status == 'QUEUED' and order.legs[0].positioneffect == 'CLOSING':
                orderrequest = baseRR.CancelOrderRequestMessage(order.orderid)
                orderrequests.append(orderrequest)

        return orderrequests

    def build_closing_orders(self) -> list[baseRR.PlaceOrderRequestMessage]:
        logger.debug("build_closing_orders")

        orderrequests = []

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(True, True)
        account = self.mediator.get_account(accountrequest)

        # Look for open positions
        for position in account.positions:
            # TODO: If positions belongs to this strat...
            if position.underlyingsymbol == self.underlying and position.putcall == 'PUT':
                # Look for closing Orders
                closingorderexists = self.check_for_closing_orders(position.symbol, account.orders)

                if closingorderexists:
                    continue

                orderrequest = baseRR.PlaceOrderRequestMessage()
                orderrequest.orderstrategytype = 'SINGLE'
                orderrequest.assettype = 'OPTION'
                orderrequest.duration = 'GOOD_TILL_CANCEL'
                orderrequest.instruction = 'BUY_TO_CLOSE'
                orderrequest.ordertype = 'LIMIT'
                orderrequest.ordersession = 'NORMAL'
                orderrequest.positioneffect = 'CLOSING'
                orderrequest.price = self.truncate(self.format_order_price(position.averageprice * (1 - float(self.profittargetpercent))), 2)
                orderrequest.quantity = position.shortquantity
                orderrequest.symbol = position.symbol

                orderrequests.append(orderrequest)

        return orderrequests

    # Order Placers
    def place_new_orders_loop(self, putorcall: str) -> None:
        # Build Order
        neworder = self.build_new_order(putorcall)

        # If neworder is None, exit.
        if neworder is None:
            return

        # Place the order and check the result
        result = self.place_order_loop(neworder)

        # If successful, return
        if result:
            return

        # Otherwise, try again
        self.place_new_orders_loop(putorcall)

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
        getorderrequest = baseRR.GetOrderRequestMessage(int(neworderresult.orderid))
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
    def get_market_session_loop(self, date: dt.datetime) -> baseRR.GetMarketHoursResponseMessage:
        request = baseRR.GetMarketHoursRequestMessage(market='OPTION', product='IND', datetime=date)
        hours = self.mediator.get_market_hours(request)

        if hours is None or hours.end < dt.datetime.now().astimezone(dt.timezone.utc):
            self.get_market_session_loop(date + dt.timedelta(days=1))

        return hours

    def check_for_closing_orders(self, symbol: str, orders: list[baseRR.AccountOrder]) -> bool:
        logger.debug("check_for_closing_orders")

        for order in orders:
            if order.status == 'QUEUED' and order.legs[0].symbol == symbol and order.legs[0].instruction == 'BUY_TO_CLOSE':
                return True

        return False

    def get_next_expiration(self, expirations: list[baseRR.GetOptionChainResponseMessage.ExpirationDate]) -> baseRR.GetOptionChainResponseMessage.ExpirationDate:
        logger.debug("get_next_expiration")

        if expirations is None:
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

    def get_best_strike(self, strikes: dict[float, baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike], buyingpower: float, liquidationvalue: float, putorcall: str) -> baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike:
        logger.debug("get_best_strike")
        # Set Variables
        bestpremium = float(0)
        beststrike = None

        if putorcall == 'PUT':
            targetdelta = self.puttargetdelta
            mindelta = self.putmindelta
        else:
            targetdelta = self.calltargetdelta
            mindelta = self.callmindelta

        # Iterate through strikes
        for strike, details in strikes.items():
            # Make sure strike delta is less then our target delta
            if (abs(details.delta) <= abs(targetdelta)) and (abs(details.delta) >= abs(mindelta)):
                # Calculate the total premium for the strike based on our buying power
                qty = self.calculate_order_quantity(strike, buyingpower, liquidationvalue)
                totalpremium = ((details.bid + details.ask) / 2) * qty

                # If the strike's premium is larger than our best premium, update it
                if totalpremium > bestpremium:
                    bestpremium = totalpremium
                    beststrike = details

        # Return the strike with the highest premium
        return beststrike

    def calculate_order_quantity(self, strike: float, buyingpower: float, liquidationvalue: float, putorcall: str) -> int:
        logger.debug("calculate_order_quantity")

        if putorcall == 'PUT':
            maxlosscalcpercent = self.putmaxlosscalcpercent
        else:
            maxlosscalcpercent = self.callmaxlosscalcpercent

        # Calculate max loss per contract
        max_loss = strike * 100 * float(maxlosscalcpercent)

        # Calculate max buying power to use
        balance_to_risk = liquidationvalue * float(self.portfolioallocationpercent)

        remainingbalance = buyingpower - (liquidationvalue - balance_to_risk)

        # Calculate trade size
        trade_size = remainingbalance // max_loss

        # Return quantity
        return int(trade_size)

    def format_order_price(self, price: float) -> float:
        logger.debug("format_order_price")

        if price > 3:
            base = .1
        else:
            base = .05

        return self.truncate(base * round(price / base), 2)

    def truncate(self, number: float, digits: int) -> float:
        logger.debug("truncate")
        stepper = 10.0 ** digits
        return math.trunc(stepper * number) / stepper
