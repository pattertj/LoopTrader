from BaseTypes.Component.abstractComponent import Component
import abc
from dataclasses import dataclass


@dataclass
class Database(abc.ABC, Component):
    connectionString: str

    @abc.abstractmethod
    def ProcessStrategy(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'ProcessStrategy' method.")