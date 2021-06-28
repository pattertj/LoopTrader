import basetypes.Mediator.reqRespTypes as baseRR
from basetypes.Strategy.singlebydeltastrategy import SingleByDeltaStrategy


def test_calculate_order_quantity():
    strat = SingleByDeltaStrategy(
        maxlosscalcpercent=0.2, portfolioallocationpercent=1.0
    )

    result = strat.calculate_order_quantity(4000, 249000, 249000)

    assert result == 3


def test_calculate_order_quantity_insufficient():
    strat = SingleByDeltaStrategy(
        maxlosscalcpercent=0.2, portfolioallocationpercent=1.0
    )

    result = strat.calculate_order_quantity(4000, 500, 500)

    assert result == 0


def test_get_best_strike():  # sourcery skip: merge-dict-assign
    strat = SingleByDeltaStrategy(
        targetdelta=-0.06,
        mindelta=-0.03,
        maxlosscalcpercent=0.2,
        portfolioallocationpercent=1.0,
    )

    strikes = {}

    strikes[4000] = new_strike(4000, 0.10, 1, 1.1)
    strikes[3090] = new_strike(3090, 0.09, 1, 1.1)
    strikes[3080] = new_strike(3080, 0.08, 1, 1.1)
    strikes[3070] = new_strike(3070, 0.07, 1, 1.1)
    strikes[3060] = new_strike(3060, 0.06, 1, 1.1)
    strikes[3050] = new_strike(3050, 0.05, 0.9, 1.0)
    strikes[3040] = new_strike(3040, 0.049, 0.8, 0.91)
    strikes[3030] = new_strike(3030, 0.045, 0.7, 0.81)
    strikes[3020] = new_strike(3020, 0.041, 0.6, 0.71)
    strikes[1010] = new_strike(1010, 0.04, 0.5, 0.61)

    strike = strat.get_best_strike(strikes, 200000, 200000)

    assert strike.strike == 1010


def new_strike(
    strike: float, delta: float, bid: float, ask: float
) -> baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike:
    new = baseRR.GetOptionChainResponseMessage.ExpirationDate.Strike()

    new.strike = strike
    new.delta = delta
    new.bid = bid
    new.ask = ask

    return new

    # def test_process_open_market(self):
    #     now = dt.datetime.now().astimezone(dt.timezone.utc)
    #     nowplus2 = dt.datetime.now().astimezone(dt.timezone.utc) + dt.timedelta(hours=2)

    #     self.func.process_open_market(nowplus2, now)
