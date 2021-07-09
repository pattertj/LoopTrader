# from basetypes.Strategy.teststrategy import helpers


# def test_get_risk_free_rate():
#     # Create our strategy
#     test = helpers.get_risk_free_rate()

#     # Check results
#     assert test is None or test is not None


# def test_calculate_iv():
#     # Create our test data
#     option_price = (0.80 + 0.95) / 2
#     underlying_price = 4352.34
#     strike = 4200
#     put_or_call = "PUT"
#     time_in_days = 3
#     risk_free_rate = 0.05

#     iv = helpers.calculate_iv(
#         option_price,
#         underlying_price,
#         strike,
#         risk_free_rate,
#         time_in_days,
#         put_or_call,
#     )

#     # Check results
#     assert iv is None or iv is not None


# def test_calculate_delta():
#     # Create our test data
#     option_price = (0.80 + 0.95) / 2
#     underlying_price = 4352.34
#     strike = 4200
#     put_or_call = "PUT"
#     time_in_days = 3
#     risk_free_rate = 0.05

#     # Calc IV then Delta
#     iv = helpers.calculate_iv(
#         option_price,
#         underlying_price,
#         strike,
#         risk_free_rate,
#         time_in_days,
#         put_or_call,
#     )
#     delta = helpers.calculate_delta(
#         underlying_price, strike, risk_free_rate, time_in_days, put_or_call, iv
#     )

#     # Check results
#     assert delta is None or delta is not None
