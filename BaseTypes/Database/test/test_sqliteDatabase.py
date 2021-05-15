import os

from BaseTypes.Database.sqliteDatabase import SqliteDatabase


def test_create_order():
    db = SqliteDatabase("testdb.db")
    result = db.create_order()

    assert result is not None
    assert result is True

    db.cursor.close()
    db.connection.close()
    os.remove("testdb.db")


def test_read_order_by_id():
    pass


def test_update_order_by_id():
    pass


def test_delete_order_by_id():
    pass


def test_create_position():
    pass


def test_read_position_by_id():
    pass


def test_update_position_by_id():
    pass


def test_delete_position_by_id():
    pass


def test_read_open_orders():
    pass


def test_read_open_positions():
    pass
