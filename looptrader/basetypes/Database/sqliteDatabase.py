import logging
import logging.config
from typing import Union
from sqlalchemy import Column, Integer, String, Table, DateTime, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapper, sessionmaker
from sqlalchemy.sql.schema import MetaData

import attr
from sqlalchemy.sql.sqltypes import Boolean
import basetypes.Mediator.reqRespTypes as baseRR
import basetypes.Mediator.baseModels as baseModels
from basetypes.Database.abstractDatabase import Database

logger = logging.getLogger("autotrader")

Base = declarative_base()
meta = MetaData()


@attr.s(auto_attribs=True)
class SqliteDatabase(Database):
    def __attrs_post_init__(self):
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
            mapper(baseModels.ExecutionLeg, execution_leg_table)
            mapper(baseModels.OrderActivity, order_activity_table)
            mapper(baseModels.OrderLeg, order_leg_table)
            # mapper(baseModels.Strategy, strat_table)
            mapper(baseModels.Order, order_table, properties={"order_legs": relationship(baseModels.OrderLeg), "order_activities": relationship(baseModels.OrderActivity), "strategy": relationship(baseModels.Strategy)})

            # Create an engine that stores data in the local directory's db file
            engine = create_engine('sqlite:///looptrader.db')

            # Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
            meta.create_all(bind=engine)

        except Exception as e:
            print(e)
            return None

    def create_order_table(self) -> Table:
        return Table(
                    'orders', 
                    meta, 
                    Column('id', Integer, primary_key=True), 
                    Column('session', String(250)),
                    Column('duration', String(250)),
                    Column('order_type', String(250)),
                    Column('quantity', Integer),
                    Column('filled_quantity', Integer),
                    Column('remaining_quantity', Integer),
                    Column('requested_destination', String(250)),
                    Column('destination_link_name', String(250)),
                    Column('price', Float),
                    Column('order_strategy_type', String(250)),
                    Column('cancelable', Boolean),
                    Column('editable', Boolean),
                    Column('status', String(250)),
                    Column('entered_time', DateTime),
                    Column('close_time', DateTime),
                    Column('account_id', Integer),
                    Column('strategy', String(250)),
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
            'orderlegs', 
            meta, 
            Column('id', Integer, primary_key=True), 
            Column('asset_type', String(250)),
            Column('cusip', String(250)),
            Column('symbol', String(250)),
            Column('description', String(250)),
            Column('instruction', String(250)),
            Column('position_effect', String(250)),
            Column('quantity', Integer),
            Column('orderid', Integer, ForeignKey("order.id"))
            )

    def create_order_activity_table(self) -> Table:
        return Table(
            'orderactivities', 
            meta, 
            Column('id', Integer, primary_key=True), 
            Column('activity_type', String(250)),
            Column('execution_type', String(250)),
            Column('quantity', Integer),
            Column('order_remaining_quantity', Integer),
            Column('orderid', Integer, ForeignKey("order.id"))
            )

    def create_execution_leg_table(self) -> Table:
        return Table(
            'executionlegs', 
            meta, 
            Column('id', Integer, primary_key=True), 
            Column('leg_id', Integer),
            Column('quantity', Integer),
            Column('mismarked_quantity', Integer),
            Column('price', Float),
            Column('time', DateTime),
            Column('orderactivityid', Integer, ForeignKey("order_activity_table.id"))
            )

    def create_order(self, request: baseRR.CreateDatabaseOrderRequest) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        engine = create_engine('sqlite:///looptrader.db')
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
        return None
