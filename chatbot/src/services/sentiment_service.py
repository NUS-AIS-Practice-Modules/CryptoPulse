from src.mock.mock_data import MOCK_SUMMARY_TEMPLATE, _make_trend

VALID_PERIODS = {"7d", "30d", "90d"}
PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def get_summary(crypto: str, period: str) -> dict:
    if period not in VALID_PERIODS:
        raise ValueError(f"Unsupported period '{period}'. Choose from {VALID_PERIODS}.")

    template = MOCK_SUMMARY_TEMPLATE[period]
    trend = _make_trend(PERIOD_DAYS[period])

    return {
        "crypto": crypto.upper(),
        "period": period,
        "overall_sentiment": template["overall_sentiment"],
        "trend": trend,
        "top_topics": template["top_topics"],
        "data_points_analyzed": template["data_points_analyzed"],
    }
