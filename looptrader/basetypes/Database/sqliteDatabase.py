import logging
import logging.config
import sqlite3
from sqlite3.dbapi2 import Connection, Cursor

import attr

from looptrader.basetypes.Database.abstractDatabase import Database

logger = logging.getLogger("autotrader")


@attr.s(auto_attribs=True)
class SqliteDatabase(Database):
    connectionstring: str = attr.ib(validator=attr.validators.instance_of(str))
    connection: Connection = attr.ib(
        validator=attr.validators.instance_of(Connection), init=False
    )
    cursor: Cursor = attr.ib(validator=attr.validators.instance_of(Cursor), init=False)

    def __attrs_post_init__(self):
        self.connection = sqlite3.connect(self.connectionstring)
        self.cursor = self.connection.cursor()
        self.pre_flight_db_check()

    # Abstract Methods
    def create_order(self) -> bool:
        query = "INSERT INTO Orders(OrderID, PositionID, Symbol, Strike, Action, Time, Quantity, Price, Commissions, UnderlyingPrice, Delta, ImpliedVolatility, Vix, ExpirationDate, PutCall) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"

        try:
            self.connection.execute(
                query,
                (
                    3,
                    1,
                    "$SPX.X",
                    4010,
                    "SELL_TO_OPEN",
                    "4/4/2021",
                    1,
                    1.35,
                    1.1,
                    4150,
                    0.0586,
                    18.2,
                    19.45,
                    "4/6/2021",
                    "P",
                ),
            )
            self.connection.commit()
        except Exception as e:
            print(e)
            return False

        return True

    def create_strategy(self, strategy_class: str, name: str, underlying: str) -> bool:
        query = "INSERT INTO Strategies(StrategyClass, StrategyName, Underlying) VALUES (?, ?, ?)"

        try:
            self.connection.execute(query, (strategy_class, name, underlying))
            self.connection.commit()
        except Exception as e:
            print(e)
            return False

        return True

    def read_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_order' method."
        )

    def update_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_order' method."
        )

    def delete_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_order' method."
        )

    def create_position(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'create_position' method."
        )

    def read_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_position' method."
        )

    def update_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_position' method."
        )

    def delete_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method."
        )

    # Class Methods

    def read_open_orders(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method."
        )

    def read_open_positions(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method."
        )

    def pre_flight_db_check(self):
        # Get all the tables
        self.cursor.execute('''SELECT * FROM sqlite_master WHERE type="table"''')

        # Identify the ones you want to check
        positionsexist = False
        ordersexist = False
        strategiesexist = False

        # Check for the required tables
        for row in self.cursor.fetchall():
            if row[1] == "Positions":
                positionsexist = True
                continue
            if row[1] == "Orders":
                ordersexist = True
                continue
            if row[1] == "Strategies":
                strategiesexist = True
                continue

        # If the Positions table is missing, create it
        if not positionsexist:
            createpositionstable = """CREATE TABLE Positions(PositionID INTEGER PRIMARY KEY, Status INTEGER, EntryOrderID INTEGER, ExitOrderID INTEGER, TargetDelta REAL)"""
            self.cursor.execute(createpositionstable)
            logger.info("Positions Table Created.")

        # If the Orders table is missing, create it
        if not ordersexist:
            createorderstable = """CREATE TABLE Orders(OrderID INTEGER PRIMARY KEY, PositionID INTEGER, Symbol TEXT, Strike REAL, Action INTEGER, Time TEXT, Quantity INTEGER, Price REAL, Commissions REAL, UnderlyingPrice REAL, Delta REAL, ImpliedVolatility REAL, Vix REAL, ExpirationDate TEXT, PutCall TEXT, FOREIGN KEY(PositionID) REFERENCES Positions(id))"""
            self.cursor.execute(createorderstable)
            logger.info("Orders Table Created.")

        # If the Strategy table is missing, create it
        if not strategiesexist:
            createorderstable = """CREATE TABLE Strategies(StrategyID INTEGER PRIMARY KEY, StrategyClass TEXT, StrategyName TEXT, Underlying TEXT)"""
            self.cursor.execute(createorderstable)
            logger.info("Strategies Table Created.")

        # Commit the changes, if they exist, to the db
        if not positionsexist or not ordersexist or not strategiesexist:
            self.connection.commit()

        # Log completion
        logger.info("Pre-Flight Checks Complete.")
