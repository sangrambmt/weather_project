from __future__ import annotations

import sys

from analysis import build_analysis_views, load_weather_data, identify_record_events


def run_query(query: str) -> str:
    normalized = query.lower().strip()
    weather_df = load_weather_data()
    last_10_days, merged_history = build_analysis_views(weather_df)

    if "hottest" in normalized and "last 10" in normalized:
        hottest_day = last_10_days.dropna(subset=["max_temp"]).sort_values(["max_temp", "date"], ascending=[False, True]).iloc[0]
        return (
            f"The hottest day in the last 10 PDF reports was {hottest_day['date'].strftime('%Y-%m-%d')}. "
            f"The observed high was {hottest_day['max_temp']:.1f}F, which was {hottest_day['high_vs_normal']:.1f}F above the normal high."
        )

    if "biggest swing" in normalized or ("swing" in normalized and "last 10" in normalized):
        biggest_swing = last_10_days.dropna(subset=["temp_swing"]).sort_values(["temp_swing", "date"], ascending=[False, True]).iloc[0]
        return (
            f"The biggest swing was on {biggest_swing['date'].strftime('%Y-%m-%d')}: "
            f"{biggest_swing['max_temp']:.1f}F high, {biggest_swing['min_temp']:.1f}F low, "
            f"for a {biggest_swing['temp_swing']:.1f}F swing."
        )

    if "warmer than average" in normalized or "days above average" in normalized:
        warmer_than_average = last_10_days[
            last_10_days["avg_temp"].notna()
            & last_10_days["effective_normal_avg_temp"].notna()
            & (last_10_days["avg_temp"] > last_10_days["effective_normal_avg_temp"])
        ]
        comparable_days = last_10_days[
            last_10_days["avg_temp"].notna() & last_10_days["effective_normal_avg_temp"].notna()
        ]
        return f"{len(warmer_than_average)} of {len(comparable_days)} comparable PDF days were warmer than the daily normal average."

    if "record" in normalized or "close to breaking" in normalized:
        findings = identify_record_events(last_10_days)
        if not findings:
            return "None of the last 10 PDF days were within 2F of an all-time record high or low."
        return "\n".join(findings)

    if "trend" in normalized or "past 3 months" in normalized:
        trend = merged_history.dropna(subset=["date", "avg_temp"]).copy()
        trend["month"] = trend["date"].dt.to_period("M").astype(str)
        monthly = trend.groupby("month", as_index=False).agg(
            avg_temp=("avg_temp", "mean"),
            max_temp=("max_temp", "max"),
            precipitation=("precipitation", "sum"),
        )
        lines = ["Past 3-month trend summary:"]
        for row in monthly.itertuples(index=False):
            lines.append(
                f"- {row.month}: avg temp {row.avg_temp:.1f}F, warmest high {row.max_temp:.1f}F, precipitation {row.precipitation:.2f} in"
            )
        return "\n".join(lines)

    if "coldest" in normalized:
        coldest = merged_history.dropna(subset=["min_temp"]).sort_values(["min_temp", "date"], ascending=[True, True]).iloc[0]
        return f"The coldest day in the 3-month history was {coldest['date'].strftime('%Y-%m-%d')} with a low of {coldest['min_temp']:.1f}F."

    return (
        "Supported questions include: hottest day in the last 10 days, biggest swing, "
        "warmer than average, record highs/lows, and past 3-month trend."
    )


def demo_questions() -> list[str]:
    return [
        "What was the hottest day in the last 10 days?",
        "Which day had the biggest swing between high and low temperature in the last 10 days?",
        "How many of the last 10 days were warmer than average?",
        "Did any of the last 10 days set or come close to breaking a record?",
        "What are the trends in the past 3 months?",
    ]


def print_demo() -> None:
    for question in demo_questions():
        print(f"Q: {question}")
        print(f"A: {run_query(question)}")
        print()


def chat() -> None:
    print("Weather chatbot ready. Type 'exit' to quit, or '--demo' to print five grounded example Q&A pairs.")
    while True:
        user_input = input("Ask a question: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        try:
            print(run_query(user_input))
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print_demo()
    else:
        chat()
