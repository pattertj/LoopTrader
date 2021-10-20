import os

from basetypes.Database.ormDatabase import ormDatabase
from basetypes.Mediator import baseModels, reqRespTypes

# def test_create_and_read_order():
#     if os.path.exists("testdb.db"):
#         os.remove("testdb.db")

#     db = ormDatabase("testdb.db")

#     queued_order = baseModels.Order()
#     queued_order.price = 1.1
#     queued_order.status = "QUEUED"
#     queued_order.strategy = 1
#     queued_order.legs = []

#     filled_order = baseModels.Order()
#     filled_order.price = 1.1
#     filled_order.status = "FILLED"
#     filled_order.strategy = 1
#     filled_order.legs = []

#     leg = baseModels.OrderLeg()
#     leg.put_call = "PUT"
#     leg.quantity = 4
#     leg.symbol = "SPX"

#     queued_order.legs.append(leg)
#     filled_order.legs.append(leg)

#     queued_request = reqRespTypes.CreateDatabaseOrderRequest(queued_order)
#     filled_request = reqRespTypes.CreateDatabaseOrderRequest(filled_order)

#     db.create_order(queued_request)
#     db.create_order(filled_request)

#     read_request = reqRespTypes.ReadDatabaseOrdersByStatusRequest(1, "QUEUED")
#     orders = db.read_order_by_status(read_request)

#     assert len(orders.orders) == 1

#     if os.path.exists("testdb.db"):
#         os.remove("testdb.db")


def test_create_and_update_order():
    if os.path.exists("testdb.db"):
        os.remove("testdb.db")

    db = ormDatabase("testdb.db")

    queued_order = baseModels.Order()
    queued_order.price = 1.1
    queued_order.status = "QUEUED"
    queued_order.strategy = 1
    queued_order.legs = []

    leg = baseModels.OrderLeg()
    leg.put_call = "PUT"
    leg.quantity = 4
    leg.symbol = "SPX"

    queued_order.legs.append(leg)

    queued_request = reqRespTypes.CreateDatabaseOrderRequest(queued_order)

    db.create_order(queued_request)

    read_request = reqRespTypes.ReadDatabaseOrdersByStatusRequest(1, "QUEUED")
    old_order = db.read_order_by_status(read_request)

    old_order.orders[0].status = "FILLED"

    update_request = reqRespTypes.UpdateDatabaseOrderRequest(old_order.orders[0])
    db.update_order(update_request)

    read_request = reqRespTypes.ReadDatabaseOrdersByStatusRequest(1, "FILLED")
    new_order = db.read_order_by_status(read_request)

    assert len(new_order.orders) == 1

    os.remove("testdb.db")
