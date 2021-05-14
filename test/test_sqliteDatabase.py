import os
import unittest

from basetypes.Database.sqliteDatabase import SqliteDatabase


class TestSqliteDatabase(unittest.TestCase):
    def setUp(self):
        self.func = SqliteDatabase("testdb.db")

    def tearDown(self):
        self.func.cursor.close()
        self.func.connection.close()
        os.remove("testdb.db")

    def test_create_order(self):
        result = self.func.create_order()

        self.assertIsNotNone(result)
        self.assertTrue(result)

    def test_read_order_by_id(self):
        pass

    def test_update_order_by_id(self):
        pass

    def test_delete_order_by_id(self):
        pass

    def test_create_position(self):
        pass

    def test_read_position_by_id(self):
        pass

    def test_update_position_by_id(self):
        pass

    def test_delete_position_by_id(self):
        pass

    def test_read_open_orders(self):
        pass

    def test_read_open_positions(self):
        pass


if __name__ == "__main__":
    unittest.main()
