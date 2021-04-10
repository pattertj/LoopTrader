import logging
from dataclasses import dataclass

import BaseTypes.Mediator.reqRespTypes as baseRR
from BaseTypes.Notifier.abstractNotifier import Notifier
from BaseTypes.Component.abstractComponent import Component

logger = logging.getLogger('autotrader')


@dataclass
class TelegramNotifier(Notifier, Component):
    client_id: str

    def do_something(self) -> None:
        pass
