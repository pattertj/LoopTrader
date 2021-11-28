import logging
import logging.config
from typing import Union

import attr
import basetypes.Mediator.baseModels as baseModels
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Database.abstractDatabase import Database
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry, relationship, sessionmaker
from sqlalchemy.sql.schema import MetaData

logger = logging.getLogger("autotrader")
Base = declarative_base()
meta = MetaData()
mapper_registry = registry()


@attr.s(auto_attribs=True)
class ormDatabase(Database):
    db_filename: str = attr.ib(validator=attr.validators.instance_of(str))
    connection_string: str = attr.ib(
        validator=attr.validators.instance_of(str), init=False
    )

    def __attrs_post_init__(self):
        self.connection_string = "sqlite:///" + self.db_filename
        self.pre_flight_db_check()

    # Setup Database
    def pre_flight_db_check(self) -> None:
        try:
            # Create Tables
            execution_leg_table = self.build_execution_leg_table()
            order_activity_table = self.build_order_activity_table()
            order_leg_table = self.build_order_leg_table()
            order_table = self.build_order_table()

            # Map Tables
            mapper_registry.map_imperatively(
                baseModels.Order,
                order_table,
                properties={
                    "legs": relationship(baseModels.OrderLeg, backref="orders"),
                    "activities": relationship(
                        baseModels.OrderActivity, backref="orders"
                    ),
                },
            )
            mapper_registry.map_imperatively(
                baseModels.OrderActivity,
                order_activity_table,
                properties={
                    "execution_legs": relationship(
                        baseModels.ExecutionLeg, backref="orderactivities"
                    ),
                },
            )
            mapper_registry.map_imperatively(baseModels.OrderLeg, order_leg_table)
            mapper_registry.map_imperatively(
                baseModels.ExecutionLeg, execution_leg_table
            )

            # Create an engine that stores data in the local directory's db file
            engine = create_engine(self.connection_string)

            # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
            meta.create_all(bind=engine)

            engine.dispose()

        except Exception as e:
            print(e)
            return None

    def build_order_table(self) -> Table:
        return Table(
            "orders",
            meta,
            Column("id", Integer, primary_key=True),
            Column("session", String(250)),
            Column("duration", String(250)),
            Column("order_type", String(250)),
            Column("quantity", Integer),
            Column("filled_quantity", Integer),
            Column("remaining_quantity", Integer),
            Column("requested_destination", String(250)),
            Column("destination_link_name", String(250)),
            Column("price", Float),
            Column("order_strategy_type", String(250)),
            Column("cancelable", Boolean),
            Column("editable", Boolean),
            Column("status", String(250)),
            Column("entered_time", DateTime),
            Column("close_time", DateTime),
            Column("order_id", Integer),
            Column("account_id", Integer),
            Column("strategy", String(250)),
        )

    def build_order_leg_table(self) -> Table:
        return Table(
            "orderlegs",
            meta,
            Column("id", Integer, primary_key=True),
            Column("asset_type", String(250)),
            Column("cusip", String(250)),
            Column("symbol", String(250)),
            Column("description", String(250)),
            Column("instruction", String(250)),
            Column("position_effect", String(250)),
            Column("quantity", Integer),
            Column("order_id", Integer, ForeignKey("orders.id")),
        )

    def build_order_activity_table(self) -> Table:
        return Table(
            "orderactivities",
            meta,
            Column("id", Integer, primary_key=True),
            Column("activity_type", String(250)),
            Column("execution_type", String(250)),
            Column("quantity", Integer),
            Column("order_remaining_quantity", Integer),
            Column("order_id", Integer, ForeignKey("orders.id")),
        )

    def build_execution_leg_table(self) -> Table:
        return Table(
            "executionlegs",
            meta,
            Column("id", Integer, primary_key=True),
            Column("leg_id", Integer),
            Column("quantity", Integer),
            Column("mismarked_quantity", Integer),
            Column("price", Float),
            Column("time", DateTime),
            Column("order_activity_id", Integer, ForeignKey("orderactivities.id")),
        )

    ###########
    # Creates #
    ###########
    def create_order(
        self, request: baseRR.CreateDatabaseOrderRequest
    ) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        # sourcery skip: class-extract-method
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.CreateDatabaseOrderResponse()

        try:
            session.add(request.order)
            session.commit()

            if request.order.id is not None:
                id: int = request.order.id
                response.id = id

        except Exception as e:
            print(e)
            session.rollback()
            return None
        finally:
            session.close()
            engine.dispose()

        return response

    def create_strategy(
        self, request: baseRR.CreateDatabaseStrategyRequest
    ) -> Union[baseRR.CreateDatabaseStrategyResponse, None]:
        # sourcery skip: class-extract-method
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.CreateDatabaseStrategyResponse()

        try:
            session.add(request.strategy)
            session.commit()

            if request.strategy.id is not None:
                id: int = request.strategy.id
                response.id = id

        except Exception as e:
            print(e)
            session.rollback()
            return None
        finally:
            session.close()
            engine.dispose()

        return response

    #########
    # Reads #
    #########
    def read_order_by_status(
        self, request: baseRR.ReadDatabaseOrdersByStatusRequest
    ) -> baseRR.ReadDatabaseOrdersByStatusResponse:
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.ReadDatabaseOrdersByStatusResponse()

        try:
            result = (
                session.query(baseModels.Order)
                .filter(
                    baseModels.Order.status == request.status
                    and baseModels.Order.strategy == request.strategy_id
                )
                .all()
            )

            session.commit()

            response.orders = result
        except Exception as e:
            print(e)
            session.rollback()
        finally:
            session.close()
            engine.dispose()

        return response

    ###########
    # Updates #
    ###########
    def update_order(self, request: baseRR.UpdateDatabaseOrderRequest):
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.CreateDatabaseOrderResponse()

        # Validate Request
        if not isinstance(request.order.id, int):
            raise ValueError("Invalid Order ID.")

        try:
            session.add(request.order)
            session.commit()

            if request.order.id is not None:
                id: int = request.order.id
                response.id = id

        except Exception as e:
            print(e)
            session.rollback()
            return None
        finally:
            session.close()
            engine.dispose()

        return response

    ###########
    # Deletes #
    ###########
