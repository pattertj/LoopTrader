from BaseTypes.Component.abstractComponent import Component
import abc
from dataclasses import dataclass


@dataclass
class Database(abc.ABC, Component):
    connectionstring: str

    @abc.abstractmethod
    def create_order(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'create_order' method.")

    @abc.abstractmethod
    def read_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_order' method.")

    @abc.abstractmethod
    def update_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_order' method.")

    @abc.abstractmethod
    def delete_order_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_order' method.")

    @abc.abstractmethod
    def create_position(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'create_position' method.")

    @abc.abstractmethod
    def read_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'read_position' method.")

    @abc.abstractmethod
    def update_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'update_position' method.")

    @abc.abstractmethod
    def delete_position_by_id(self) -> bool:
        raise NotImplementedError(
            "Each strategy must implement the 'delete_position' method.")
