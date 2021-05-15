import abc

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Notifier(abc.ABC, Component):

    @abc.abstractmethod
    def send_notification(self, request: baseRR.SendNotificationRequestMessage) -> None:
        '''Method to handle bot requests to push notifications'''
        raise NotImplementedError(
            "Each strategy must implement the 'do_something' method.")
