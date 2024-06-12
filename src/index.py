from fastapi import FastAPI, HTTPException, File, UploadFile, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import io
import pandas as pd
from pytrends.request import TrendReq
from src.dtos.ISayHelloDto import ISayHelloDto

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/hello")
async def hello_message(dto: ISayHelloDto):
    return {"message": f"Hello {dto.message}"}


# Define Pydantic models for request data validation
class KeywordRequest(BaseModel):
    keyword: str
    geo: str = 'GB'

class TrendDataRequest(BaseModel):
    keywords: List[str]
    timeframe: str
    geo: str

# Endpoint to get top trending keywords
@app.get("/top-trending-keywords/")
async def get_top_trending_keywords():
    pytrends = TrendReq(hl='en-US', tz=360)
    trending_searches = pytrends.trending_searches(pn='united_kingdom')
    top_trending_keywords = list(trending_searches.head(10).itertuples(index=False, name=None))
    return {"top_trending_keywords": top_trending_keywords}

# Endpoint to get related trending keywords for a specific keyword
@app.get("/trending-keywords/{keyword}", response_model=KeywordRequest)
async def get_trending_keywords(keyword: str, geo: str = 'GB'):
    pytrends = TrendReq(hl='en-GB', tz=0)
    pytrends.build_payload([keyword], timeframe='now 1-d', geo=geo)
    trending_data = pytrends.related_queries()
    related_keywords = trending_data.get(keyword, {}).get('top', {}).get('query', [])
    return {"trending_keywords": related_keywords}

# Endpoint to download trends data as a CSV file
@app.post("/trends-data/")
async def download_trends_data(data: TrendDataRequest):
    keywords = data.keywords
    timeframe = data.timeframe
    geo = data.geo

    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
    interest_over_time_df = pytrends.interest_over_time()

    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    interest_over_time_df.to_csv(csv_buffer, index=False)

    # Prepare the StreamingResponse
    response = StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trends_data.csv"}
    )

    return response
