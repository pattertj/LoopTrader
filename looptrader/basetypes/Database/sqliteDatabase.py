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


class Order:
    pass


@attr.s(auto_attribs=True)
class SqliteDatabase(Database):
    db_filename: str = attr.ib(validator=attr.validators.instance_of(str))
    connection_string: str = attr.ib(
        validator=attr.validators.instance_of(str), init=False
    )

    def __attrs_post_init__(self):
        self.connection_string = "sqlite:///" + self.db_filename
        self.pre_flight_db_check()

    # Abstract Methods
    def pre_flight_db_check(self) -> None:
        try:
            # Create Tables
            execution_leg_table = self.create_execution_leg_table()
            order_activity_table = self.create_order_activity_table()
            order_leg_table = self.create_order_leg_table()
            # strat_table = self.create_strategy_table()
            order_table = self.create_order_table()

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

            # mapper_registry.map_imperatively(baseModels.Strategy, strat_table)

            # Create an engine that stores data in the local directory's db file
            engine = create_engine(self.connection_string)

            # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
            meta.create_all(bind=engine)

            engine.dispose()

        except Exception as e:
            print(e)
            return None

    def create_order_table(self) -> Table:
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

    # def create_strategy_table(self) -> Table:
    #     return Table(
    #         'strategies',
    #         meta,
    #         Column('id', Integer, primary_key=True),
    #         Column('name', String)
    #         )

    def create_order_leg_table(self) -> Table:
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

    def create_order_activity_table(self) -> Table:
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

    def create_execution_leg_table(self) -> Table:
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

    def create_order(
        self, request: baseRR.CreateDatabaseOrderRequest
    ) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession()

        try:
            session.add(request.order)
        except Exception as e:
            print(e)
            session.rollback()
            return None

        session.commit()
        engine.dispose()
        return None

    def read_open_orders(self) -> Union[None, list[baseModels.Order]]:
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        result = None

        try:
            result = (
                session.query(baseModels.Order)
                .filter(baseModels.Order.status == "QUEUED")
                .all()
            )
        except Exception as e:
            print(e)
            session.rollback()
        finally:
            session.close()
            engine.dispose()

        return result
