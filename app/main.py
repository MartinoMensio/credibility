from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from .routers import sources, origins, urls, domains, utils

app = FastAPI()

app.include_router(sources.router, prefix='/sources', tags=['sources'])
app.include_router(origins.router, prefix='/origins', tags=['origins'])
app.include_router(domains.router, prefix='/domains', tags=['domains'])
app.include_router(urls.router, prefix='/urls', tags=['urls'])
app.include_router(utils.router, prefix='/utils', tags=['utils'])

@app.get('/')
async def root():
    return {
        'name': 'credibility',
        'docs': '/docs'
    }
