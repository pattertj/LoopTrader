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


@attr.s(auto_attribs=True)
class SpreadsByDeltaStrategy(Strategy, Component):
    """The concrete implementation of the generic LoopTrader Strategy class for trading Cash-Secured Puts by Delta."""

    strategy_name: str = attr.ib(
        default="Sample Spread Strategy", validator=attr.validators.instance_of(str)
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
    targetdelta: float = attr.ib(
        default=-0.1, validator=attr.validators.instance_of(float)
    )
    minimumdte: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    maximumdte: int = attr.ib(default=4, validator=attr.validators.instance_of(int))
    maxlosscalcpercent: float = attr.ib(
        default=0.1, validator=attr.validators.instance_of(float)
    )
    openingorderloopseconds: int = attr.ib(
        default=20, validator=attr.validators.instance_of(int)
    )
    sleepuntil: dt.datetime = attr.ib(
        init=False,
        default=dt.datetime.now().astimezone(dt.timezone.utc),
        validator=attr.validators.instance_of(dt.datetime),
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

        # If the next market session is not today, wait until 30minutes before close
        if hours.start.day != now.day:
            self.sleepuntil = hours.end - dt.timedelta(minutes=30)
            logger.info(
                "Markets are closed until {}. Sleeping until {}".format(
                    hours.start, self.sleepuntil
                )
            )
            return

        # If In-Market
        elif (hours.end - dt.timedelta(minutes=30)) < now < hours.end:
            self.process_open_market(hours.end, now)

    def process_open_market(self, close: dt.datetime, now: dt.datetime):
        """Open Market Trading Logic"""
        logger.debug("Processing Open-Market")

        # Place New Orders
        self.place_new_orders_loop()

    def build_new_order(self) -> Union[baseRR.PlaceOrderRequestMessage, None]:
        """Trading Logic for building new Order Request Messages"""
        logger.debug("build_new_order")

        # Get account balance
        accountrequest = baseRR.GetAccountRequestMessage(False, True)
        account = self.mediator.get_account(accountrequest)

        if account is None:
            logger.error("Failed to get Account")
            return None

        # Calculate trade date
        startdate = dt.date.today() + dt.timedelta(days=self.minimumdte)
        enddate = dt.date.today() + dt.timedelta(days=self.maximumdte)

        # Get option chain
        chainrequest = baseRR.GetOptionChainRequestMessage(
            contracttype="PUT",
            fromdate=startdate,
            todate=enddate,
            symbol=self.underlying,
            includequotes=False,
            optionrange="OTM",
        )

        chain = self.mediator.get_option_chain(chainrequest)

        # Should we even try?
        usedbp = 0.0
        for position in account.positions:
            if (
                position.underlyingsymbol == self.underlying
                and position.putcall == "PUT"
            ):
                usedbp += (
                    int(position.symbol[-4:])
                    * 100
                    * position.shortquantity
                    * self.maxlosscalcpercent
                )

        estbp = 0.9 * (chain.underlyinglastprice * 0.2 * 100)
        availbp = account.currentbalances.liquidationvalue - usedbp

        if estbp > availbp:
            return None

        # Find expiration to trade
        expiration = self.get_next_expiration(chain.putexpdatemap)

        # If no valid expirations, exit.
        if expiration is None:
            return None

        # Get the best strike
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

        # If no valid qty, exit.
        if qty is None or qty == 0:
            return None

        # Calculate price
        price = (strike.bid + strike.ask) / 2
        formattedprice = self.format_order_price(price)

        # Build Order
        orderrequest = baseRR.PlaceOrderRequestMessage()
        orderrequest.orderstrategytype = "SINGLE"
        orderrequest.assettype = "OPTION"
        orderrequest.duration = "GOOD_TILL_CANCEL"
        orderrequest.instruction = "SELL_TO_OPEN"
        orderrequest.ordertype = "LIMIT"
        orderrequest.ordersession = "NORMAL"
        orderrequest.positioneffect = "OPENING"
        orderrequest.price = formattedprice
        orderrequest.quantity = qty
        orderrequest.symbol = strike.symbol

        # Return Order
        return orderrequest

    # Order Placers
    def place_new_orders_loop(self) -> None:
        """Looping Logic for placing new orders"""
        # Build Order
        neworder = self.build_new_order()

        # If there isn't an order, exit.
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
        if neworderresult.orderid is None or neworderresult.orderid == 0:
            return False

        # Wait to let the Order process
        time.sleep(self.openingorderloopseconds)

        # Fetch the Order status
        getorderrequest = baseRR.GetOrderRequestMessage(int(neworderresult.orderid))
        processedorder = self.mediator.get_order(getorderrequest)

        # If the order isn't filled
        if processedorder.status != "FILLED":
            # Cancel it
            cancelorderrequest = baseRR.CancelOrderRequestMessage(
                neworderresult.orderid
            )
            self.mediator.cancel_order(cancelorderrequest)

            # Return failure to fill order
            return False

        # TODO: Fix
        notification = baseRR.SendNotificationRequestMessage(
            "Sold <code>- {}x {} @ ${}</code>".format(
                str(orderrequest.quantity),
                str(orderrequest.symbol),
                "{:,.2f}".format(orderrequest.price),
            )
        )
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
            market="OPTION", product="IND", datetime=date
        )

        hours = self.mediator.get_market_hours(request)

        if hours is None or hours.end < dt.datetime.now().astimezone(dt.timezone.utc):
            return self.get_market_session_loop(date + dt.timedelta(days=1))

        return hours

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
            if abs(details.delta) <= abs(self.targetdelta):
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

    def calculate_order_quantity(
        self,
        shortstrike: float,
        longstrike: float,
        buyingpower: float,
        liquidationvalue: float,
    ) -> int:
        """Calculates the number of positions to open for a given account and strike."""
        logger.debug("calculate_order_quantity")

        # Calculate max loss per contract
        max_loss = abs(shortstrike - longstrike) * 100

        # Calculate max buying power to use
        balance_to_risk = liquidationvalue * float(self.portfolioallocationpercent)

        remainingbalance = buyingpower - (liquidationvalue - balance_to_risk)

        # Calculate trade size
        trade_size = remainingbalance // max_loss

        # Log Values
        logger.info(
            "Short Strike: {} Long Strike: {} BuyingPower: {} LiquidationValue: {} MaxLoss: {} BalanceToRisk: {} RemainingBalance: {} TradeSize: {} ".format(
                shortstrike,
                longstrike,
                buyingpower,
                liquidationvalue,
                max_loss,
                balance_to_risk,
                remainingbalance,
                trade_size,
            )
        )

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
