import os

from basetypes.Database.sqliteDatabase import SqliteDatabase
from basetypes.Mediator import baseModels, reqRespTypes


def test_create_and_read_order():
    if os.path.exists("testdb.db"):
        os.remove("testdb.db")
    db = SqliteDatabase("testdb.db")

    queued_order = baseModels.Order()
    queued_order.price = 1.1
    queued_order.status = "QUEUED"
    queued_order.legs = []

    filled_order = baseModels.Order()
    filled_order.price = 1.1
    filled_order.status = "FILLED"
    filled_order.legs = []

    leg = baseModels.OrderLeg()
    leg.put_call = "PUT"
    leg.quantity = 4
    leg.symbol = "SPX"

    queued_order.legs.append(leg)
    filled_order.legs.append(leg)

    queued_request = reqRespTypes.CreateDatabaseOrderRequest(queued_order)
    filled_request = reqRespTypes.CreateDatabaseOrderRequest(filled_order)

    db.create_order(queued_request)
    db.create_order(filled_request)

    orders = db.read_open_orders()

    assert len(orders) == 1

    os.remove("testdb.db")


# def test_create_order():
#     db = SqliteDatabase("testdb.db")

#     strat_request = baseRR.CreateDatabaseStrategyRequest("TESTING")
#     strat_result = db.create_strategy(strat_request)

#     assert strat_result is not None
#     assert strat_result.strategy_id >= 0

#     order_request = baseRR.CreateDatabaseOrderRequest(
#         123, strat_result.strategy_id, "PENDING"
#     )
#     order_result = db.create_order(order_request)

#     assert order_result is not None
#     assert order_result.order_id >= 0

#     db.cursor.close()
#     db.connection.close()
#     os.remove("testdb.db")


# def test_create_position():
#     db = SqliteDatabase("testdb.db")

#     strat_request = baseRR.CreateDatabaseStrategyRequest("TESTING")
#     strat_result = db.create_strategy(strat_request)

#     assert strat_result is not None
#     assert strat_result.strategy_id >= 0

#     order_request = baseRR.CreateDatabaseOrderRequest(
#         123, strat_result.strategy_id, "PENDING"
#     )
#     order_result = db.create_order(order_request)

#     assert order_result is not None
#     assert order_result.order_id >= 0

#     position_request = baseRR.CreateDatabasePositionRequest(
#         strat_result.strategy_id, "SPX", 5, False, order_result.order_id, 0
#     )
#     position_result = db.create_position(position_request)

#     assert position_result is not None
#     assert position_result.position_id >= 0

#     db.cursor.close()
#     db.connection.close()
#     os.remove("testdb.db")


# def test_read_all_positions_for_strategy_id():
#     db = SqliteDatabase("testdb.db")

#     strat_request = baseRR.CreateDatabaseStrategyRequest("TESTING")
#     strat_result = db.create_strategy(strat_request)

#     assert strat_result is not None
#     assert strat_result.strategy_id >= 0

#     order_request = baseRR.CreateDatabaseOrderRequest(
#         123, strat_result.strategy_id, "PENDING"
#     )
#     order_result = db.create_order(order_request)

#     assert order_result is not None
#     assert order_result.order_id >= 0

#     position_request = baseRR.CreateDatabasePositionRequest(
#         strat_result.strategy_id, "SPX", 5, True, order_result.order_id, 0
#     )
#     position_result = db.create_position(position_request)

#     position_request = baseRR.CreateDatabasePositionRequest(
#         strat_result.strategy_id + 1, "SPX", 5, True, order_result.order_id, 0
#     )
#     position_result = db.create_position(position_request)

#     position_request = baseRR.CreateDatabasePositionRequest(
#         strat_result.strategy_id, "SPX", 5, True, order_result.order_id, 0
#     )
#     position_result = db.create_position(position_request)

#     position_request = baseRR.CreateDatabasePositionRequest(
#         strat_result.strategy_id, "SPX", 5, False, order_result.order_id, 0
#     )
#     position_result = db.create_position(position_request)

#     assert position_result is not None
#     assert position_result.position_id >= 0

#     read = baseRR.ReadOpenPositionsByStrategyIDRequest(strat_result.strategy_id)
#     read_result = db.read_open_positions_by_strategy_id(read)

#     assert read_result is not None

#     db.cursor.close()
#     db.connection.close()
#     os.remove("testdb.db")


# # def test_create_order():
# #     db = SqliteDatabase("testdb.db")
# #     result = db.create_order()

# #     assert result is not None
# #     assert result is True

# #     db.cursor.close()
# #     db.connection.close()
# #     os.remove("testdb.db")


# # def test_read_order_by_id():
# #     pass


# # def test_update_order_by_id():
# #     pass


# # def test_delete_order_by_id():
# #     pass


# # def test_create_position():
# #     pass


# # def test_read_position_by_id():
# #     pass


# # def test_update_position_by_id():
# #     pass


# # def test_delete_position_by_id():
# #     pass


# # def test_read_open_orders():
# #     pass


# # def test_read_open_positions():
# #     pass
