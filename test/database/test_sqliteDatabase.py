# import os

# import basetypes.Mediator.reqRespTypes as baseRR
# from basetypes.Database.sqliteDatabase import SqliteDatabase


# def test_create_strategy():
#     db = SqliteDatabase("testdb.db")

#     request = baseRR.CreateDatabaseStrategyRequest("TESTING")
#     result = db.create_strategy(request)

#     assert result is not None
#     assert result.strategy_id >= 0

#     db.cursor.close()
#     db.connection.close()
#     os.remove("testdb.db")


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
