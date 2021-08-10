from datetime import datetime
import logging
import logging.config
import sqlite3
from sqlite3.dbapi2 import Connection, Cursor
from typing import Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Database.abstractDatabase import Database

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
    # STRATEGY FUNCTIONS
    def create_strategy(
        self, request: baseRR.CreateDatabaseStrategyRequest
    ) -> Union[baseRR.CreateDatabaseStrategyResponse, None]:
        query = "INSERT INTO Strategies(StrategyName) VALUES (?)"

        try:
            self.cursor.execute(query, (request.strategy_name,))
            self.connection.commit()
        except Exception as e:
            print(e)
            return None

        return baseRR.CreateDatabaseStrategyResponse(self.cursor.lastrowid)

    def read_strategy_by_name(self, name: str) -> Union[list, None]:
        query = "SELECT * FROM Strategies WHERE StrategyName=?"

        try:
            self.cursor.execute(query, (name,))
            results = self.cursor.fetchall()
        except Exception as e:
            print(e)
            return None

        return results

    # ORDER FUNCTIONS
    def create_order(
        self, request: baseRR.CreateDatabaseOrderRequest
    ) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        query = (
            "INSERT INTO Orders(StrategyID, BrokerOrderNumber, Status) VALUES (?,?,?)"
        )

        try:
            self.cursor.execute(
                query,
                (
                    request.strategy_id,
                    request.broker_order_number,
                    request.status,
                ),
            )
            self.connection.commit()
        except Exception as e:
            print(e)
            return None

        return baseRR.CreateDatabaseOrderResponse(self.cursor.lastrowid)

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

    def read_open_orders(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method."
        )

    def read_open_orders_by_strategy_id(
        self, request: baseRR.ReadOrdersByStrategyIDRequest
    ) -> Union[baseRR.ReadOrdersByStrategyIDResponse, None]:
        query = "SELECT * FROM Orders WHERE Status<>'FILLED' AND StrategyID=?"

        try:
            self.cursor.execute(query, (request.strategy_id,))
            results = self.cursor.fetchall()
        except Exception as e:
            print(e)
            return None

        response = baseRR.ReadOrdersByStrategyIDResponse()
        response.orders = results

        return response

    # POSITION FUNCTIONS
    def create_position(
        self, request: baseRR.CreateDatabasePositionRequest
    ) -> Union[baseRR.CreateDatabasePositionResponse, None]:
        query = "INSERT INTO Positions(StrategyID, Symbol, Quantity, IsOpen, ExpirationDate, Price, EntryOrderID, ExitOrderID) VALUES (?,?,?,?,?,?,?,?)"

        try:
            self.cursor.execute(
                query,
                (
                    request.strategy_id,
                    request.symbol,
                    request.quantity,
                    request.is_open,
                    str(request.expiration_date),
                    request.price,
                    request.entry_order_id,
                    request.exit_order_id,
                ),
            )
            self.connection.commit()
        except Exception as e:
            print(e)
            return None

        return baseRR.CreateDatabasePositionResponse(self.cursor.lastrowid)

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

    def read_open_positions_by_strategy_id(
        self, request: baseRR.ReadOpenPositionsByStrategyIDRequest
    ) -> Union[baseRR.ReadOpenPositionsByStrategyIDResponse, None]:
        query = "SELECT * FROM Positions WHERE IsOpen = 1 AND StrategyID=?"

        try:
            self.cursor.execute(query, (request.strategy_id,))
            results = self.cursor.fetchall()
        except Exception as e:
            print(e)
            return None

        response = baseRR.ReadOpenPositionsByStrategyIDResponse()
        response.positions = []

        for result in results:
            position = baseRR.DatabasePosition()
            position.position_id = result[0]
            position.strategy_id = result[1]
            position.symbol = result[2]
            position.quantity = result[3]
            position.is_open = result[4]
            position.expiration_date = datetime.strptime(result[5], "%Y-%m-%d 00:00:00")
            position.price = result[6]
            position.entry_order_id = result[7]
            position.exit_order_id = result[8]
            response.positions.append(position)

        return response

    # Class Methods
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
            createpositionstable = """CREATE TABLE Positions(PositionID INTEGER PRIMARY KEY, StrategyID INTEGER, Symbol TEXT, Quantity INTEGER, IsOpen INTEGER, ExpirationDate TEXT, Price REAL, EntryOrderID INTEGER, ExitOrderID INTEGER, FOREIGN KEY(EntryOrderID) REFERENCES Orders(OrderID), FOREIGN KEY(ExitOrderID) REFERENCES Orders(OrderID), FOREIGN KEY(StrategyID) REFERENCES Strategies(StrategyID))"""
            self.cursor.execute(createpositionstable)
            logger.info("Positions Table Created.")

        # If the Orders table is missing, create it
        if not ordersexist:
            createorderstable = """CREATE TABLE Orders(OrderID INTEGER PRIMARY KEY, StrategyID INTEGER, BrokerOrderNumber INTEGER, Status TEXT, FOREIGN KEY(StrategyID) REFERENCES Strategies(StrategyID))"""
            self.cursor.execute(createorderstable)
            logger.info("Orders Table Created.")

        # If the Strategy table is missing, create it
        if not strategiesexist:
            createstrategiestable = """CREATE TABLE Strategies(StrategyID INTEGER PRIMARY KEY, StrategyName TEXT)"""
            self.cursor.execute(createstrategiestable)
            logger.info("Strategies Table Created.")

        # Commit the changes, if they exist, to the db
        if not positionsexist or not ordersexist or not strategiesexist:
            self.connection.commit()

        # Log completion
        logger.info("Pre-Flight Checks Complete.")
