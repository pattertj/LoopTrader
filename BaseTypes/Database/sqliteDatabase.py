from sqlite3.dbapi2 import Connection, Cursor
from BaseTypes.Database.abstractDatabase import Database
from dataclasses import dataclass, field
import sqlite3


@dataclass
class SqliteDatabase(Database):
    connectionstring: str
    connection: Connection = field(init=False)
    cursor: Cursor = field(init=False)

    def __post_init__(self):
        self.connection = sqlite3.connect(self.connectionstring)
        self.cursor = self.connection.cursor()

    # Abstract Methods
    def create_order(self) -> bool:
        query = "INSERT INTO Orders(OrderID, PositionID, Symbol, Strike, Action, Time, Quantity, Price, Commissions, UnderlyingPrice, Delta, ImpliedVolatility, Vix, ExpirationDate, PutCall) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

        self.connection.execute(query, (1, 1, '$SPX.X', 4010, 'SELL_TO_OPEN', '4/4/2021', 1, 1.35, 1.1, 4150, .0586, 18.2, 19.45, '4/6/2021', 'P'))
        self.connection.commit()

    def read_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_order' method.")

    def update_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_order' method.")

    def delete_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_order' method.")

    def create_position(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'create_position' method.")

    def read_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_position' method.")

    def update_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_position' method.")

    def delete_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method.")

    # Class Methods

    def read_open_orders(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method.")

    def read_open_positions(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method.")
