import asyncio

from pytrends_httpx.request import TrendReq
from pytrends_httpx.dailydata import get_daily_data

async def main():
    # Only need to run this once, the rest of requests will use the same session.
    pytrend = TrendReq()

    # Create payload and capture API tokens. Only needed for interest_over_time(), interest_by_region() & related_queries()
    await pytrend.build_payload(kw_list=['pizza', 'bagel'])

    # Interest Over Time
    interest_over_time_df = await pytrend.interest_over_time()
    print(interest_over_time_df.head())

    # Interest by Region
    interest_by_region_df = await pytrend.interest_by_region()
    print(interest_by_region_df.head())

    # Related Queries, returns a dictionary of dataframes
    related_queries_dict = await pytrend.related_queries()
    print(related_queries_dict)

    # Get Google Hot Trends data
    trending_searches_df = await pytrend.trending_searches()
    print(trending_searches_df.head())

    # Get Google Hot Trends data
    today_searches_df = await pytrend.today_searches()
    print(today_searches_df.head())

    # Get Google Top Charts
    top_charts_df = await pytrend.top_charts(2018, hl='en-US', tz=300, geo='GLOBAL')
    print(top_charts_df.head())

    # Get Google Keyword Suggestions
    suggestions_dict = await pytrend.suggestions(keyword='pizza')
    print(suggestions_dict)

    daily_data = await get_daily_data('pizza', 2021, 1, 2021, 1)
    print(daily_data.head())

asyncio.run(main())
