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
from sqlalchemy.orm import joinedload, registry, relationship, sessionmaker
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
        self.connection_string = f"sqlite:///{self.db_filename}"
        self.pre_flight_db_check()

    ##################
    # Setup Database #
    ##################
    def pre_flight_db_check(self) -> None:
        try:
            # Create Tables
            execution_leg_table = self.build_execution_leg_table()
            order_activity_table = self.build_order_activity_table()
            order_leg_table = self.build_order_leg_table()
            order_table = self.build_order_table()
            strategy_table = self.build_strategy_table()

            # Map Tables
            mapper_registry.map_imperatively(
                baseModels.Order,
                order_table,
                properties={
                    "legs": relationship(baseModels.OrderLeg, backref="orders"),
                    "activities": relationship(
                        baseModels.OrderActivity, backref="orders"
                    ),
                    "strategy": relationship(
                        baseModels.Strategy, backref="orders", uselist=False
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
            mapper_registry.map_imperatively(baseModels.Strategy, strategy_table)

            # Create an engine that stores data in the local directory's db file
            engine = create_engine(self.connection_string)

            # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
            meta.create_all(bind=engine)

            engine.dispose()

        except Exception as e:
            print(e)
            return None

    def build_strategy_table(self) -> Table:
        return Table(
            "strategies",
            meta,
            Column("id", Integer, primary_key=True),
            Column("name", String(250)),
        )

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
            Column("strategy_id", Integer, ForeignKey("strategies.id")),
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
            Column("leg_id", Integer),
            Column("position_effect", String(250)),
            Column("put_call", String(250)),
            Column("quantity", Integer),
            Column("expiration_date", DateTime),
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
            Column("orderactivity_id", Integer, ForeignKey("orderactivities.id")),
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
            # Add Order
            session.add(request.order)

            # Add Legs
            for leg in request.order.legs:
                session.add(leg)

            # Add Activities
            for activity in request.order.activities:
                session.add(activity)

            # Commit Inserts
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
                .options(joinedload(baseModels.Order.legs))
                .filter(
                    baseModels.Order.status == request.status
                    and baseModels.Order.strategy_id == request.strategy_id
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

    def read_active_orders(
        self, request: baseRR.ReadOpenDatabaseOrdersRequest
    ) -> baseRR.ReadOpenDatabaseOrdersResponse:
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.ReadOpenDatabaseOrdersResponse()
        response.orders = []

        try:
            result = (
                session.query(baseModels.Order)
                .options(joinedload(baseModels.Order.legs))
                .filter(baseModels.Order.strategy_id == request.strategy_id)
                .filter(baseModels.Order.status != "REJECTED")
                .filter(baseModels.Order.status != "CANCELED")
                .filter(baseModels.Order.status != "FILLED")
                .filter(baseModels.Order.status != "EXPIRED")
                .filter(baseModels.Order.status != "REPLACED")
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

    def read_first_strategy_by_name(
        self, request: baseRR.ReadDatabaseStrategyByNameRequest
    ) -> Union[baseRR.ReadDatabaseStrategyByNameResponse, None]:
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.ReadDatabaseStrategyByNameResponse()
        response.strategy = baseModels.Strategy()

        try:
            result = (
                session.query(baseModels.Strategy)
                .filter(baseModels.Strategy.name == request.name)
                .first()
            )

            session.commit()

            response.strategy = result
        except Exception as e:
            print(e)
            session.rollback()
        finally:
            session.close()
            engine.dispose()

        return response

    def read_offset_legs_by_expiration(
        self, request: baseRR.ReadOffsetLegsByExpirationRequest
    ) -> baseRR.ReadOffsetLegsByExpirationResponse:
        # Setup DB Session
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)

        # Build Response
        response = baseRR.ReadOffsetLegsByExpirationResponse()

        try:
            result = (
                session.query(baseModels.OrderLeg)
                .join(baseModels.Order)
                .filter(baseModels.Order.id == baseModels.OrderLeg.order_id)
                .filter(baseModels.Order.strategy_id == request.strategy_id)
                .filter(baseModels.Order.status == "FILLED")
                .filter(baseModels.OrderLeg.expiration_date == request.expiration)
                .filter(baseModels.OrderLeg.put_call == request.put_or_call)
                .filter(baseModels.OrderLeg.instruction == "BUY_TO_OPEN")
                .all()
            )

            session.commit()

            response.offset_legs = result
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
    def update_order(
        self, request: baseRR.UpdateDatabaseOrderRequest
    ) -> Union[baseRR.UpdateDatabaseOrderResponse, None]:
        # sourcery skip: class-extract-method
        engine = create_engine(self.connection_string)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession(expire_on_commit=False)
        response = baseRR.UpdateDatabaseOrderResponse()

        try:
            # Add Order
            session.merge(request.order)

            # Add Legs
            for leg in request.order.legs:
                session.merge(leg)

            # Add Activities
            for activity in request.order.activities:
                session.merge(activity)

            # Commit Inserts
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
