import abc

import attr
from BaseTypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Notifier(abc.ABC, Component):

    @abc.abstractmethod
    def send_notification(self) -> None:
        raise NotImplementedError(
            "Each strategy must implement the 'do_something' method.")
