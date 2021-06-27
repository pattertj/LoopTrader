import abc

import attr
from basetypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True, eq=False)
class Strategy(abc.ABC, Component):
    """
    The Strategy class provides the basic framework of a strategy that can be extended to many option trading strategies.
    """

    strategy_name: str = attr.ib(validator=attr.validators.instance_of(str))
    underlying: str = attr.ib(validator=attr.validators.instance_of(str))
    strategy_id: int = attr.ib(default=-1, validator=attr.validators.instance_of(int))

    @abc.abstractmethod
    def process_strategy(self):
        raise NotImplementedError("Each strategy must implement the 'ProcessStrategy' method.")
