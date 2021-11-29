import abc
from typing import Union

import attr
import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Component.abstractComponent import Component


@attr.s(auto_attribs=True)
class Database(abc.ABC, Component):
    @abc.abstractmethod
    def create_order(
        self, request: baseRR.CreateDatabaseOrderRequest
    ) -> Union[baseRR.CreateDatabaseOrderResponse, None]:
        raise NotImplementedError(
            "Each database must implement the 'create_order' method."
        )

    @abc.abstractmethod
    def create_strategy(
        self, request: baseRR.CreateDatabaseStrategyRequest
    ) -> Union[baseRR.CreateDatabaseStrategyResponse, None]:
        raise NotImplementedError(
            "Each database must implement the 'create_strategy' method."
        )

    @abc.abstractmethod
    def read_first_strategy_by_name(
        self, request: baseRR.ReadDatabaseStrategyByNameRequest
    ) -> Union[baseRR.ReadDatabaseStrategyByNameResponse, None]:
        raise NotImplementedError(
            "Each database must implement the 'read_strategy_by_name' method."
        )
