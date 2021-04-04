from BaseTypes.Mediator.abstractMediator import Mediator
from BaseTypes.Database.abstractDatabase import Database
from dataclasses import dataclass


@dataclass
class SqliteDatabase(Database):
    connectionString: str = 'foo'

    def ProcessStrategy(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'ProcessStrategy' method.")