import logging
import logging.config
from dataclasses import dataclass

from BaseTypes.Component.abstractComponent import Component
from BaseTypes.Strategy.abstractStrategy import Strategy

logger = logging.getLogger('autotrader')


@dataclass
class CspStrategy(Strategy, Component):
    strategy_name: str = 'foo'
    underlying: str = "$SPX.X"
    portfolioallocationpercent: float = 1.0
    buy_or_sell: str = 'Sell'
    targetdelta: float = .06
    minimumdte: int = 1
    maximumdte: int = 4
    profittargetpercent: float = .7
    maxlosscalcpercent: float = .2
    openingorderloopseconds: int = 10

    def processstrategy(self) -> bool:
        # Check if the markets are open

        # Pre-Market
        #   Exit.

        # In-Market
        #   If 15min from close
        #       Open expiring positions should be off-set to free-up buying power

        #   Check for open positions, and open positions if needed

        #   If 15min from close
        #       Cancel closing orders
        #   Else
        #       Check for closing orders on open positions, and open orders if needed

        # After-Hours
        #   If within 15min after close
        #       Re-open closing orders
        #   Else
        #       Exit.

        pass
