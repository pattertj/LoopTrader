from BaseTypes.Component.abstractComponent import Component
import abc
from dataclasses import dataclass


@dataclass
class Strategy(abc.ABC, Component):
    """
    The Strategy class provides the basic framework of a strategy that can be extended to many option trading strategies.
    """
    strategy_name: str
    underlying: str

    @abc.abstractmethod
    def processstrategy(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'ProcessStrategy' method.")
