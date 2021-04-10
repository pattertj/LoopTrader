from BaseTypes.Component.abstractComponent import Component
import abc
from dataclasses import dataclass

import BaseTypes.Mediator.reqRespTypes as baseRR


@dataclass
class Notifier(abc.ABC, Component):
    client_id: str

    @abc.abstractmethod
    def do_something(self) -> None:
        raise NotImplementedError(
            "Each strategy must implement the 'do_something' method.")