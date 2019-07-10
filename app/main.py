from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .routers import sources, origins

app = FastAPI()

app.include_router(sources.router, prefix='/sources', tags=['sources'])
app.include_router(origins.router, prefix='/origins', tags=['origins'])

@app.get('/')
async def root():
    return {
        'name': 'twitter_connector',
        'docs': '/docs'
    }
