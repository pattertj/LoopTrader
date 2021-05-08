import abc

import attr
import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Notifier(abc.ABC, Component):

    @abc.abstractmethod
    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        raise NotImplementedError(
            "Each strategy must implement the 'do_something' method.")
