from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .routers import sources

app = FastAPI()

app.include_router(sources.router, prefix='/sources', tags=['sources'])

@app.get('/')
async def root():
    return {
        'name': 'twitter_connector',
        'docs': '/docs'
    }