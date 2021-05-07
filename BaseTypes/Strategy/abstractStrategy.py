import abc

import attr
from BaseTypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Strategy(abc.ABC, Component):
    """
    The Strategy class provides the basic framework of a strategy that can be extended to many option trading strategies.
    """
    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    underlying: str = attr.ib(validator=attr.validators.instance_of(str))

    @abc.abstractmethod
    def process_strategy(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'ProcessStrategy' method.")
