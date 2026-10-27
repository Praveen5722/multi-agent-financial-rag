import os, httpx

async def search_news(query: str) -> list[dict]:
    """Optional current-news lookup via Tavily. Empty when no key is configured."""
    key = os.getenv('TAVILY_API_KEY')
    if not key: return []
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post('https://api.tavily.com/search', json={'api_key':key,'query':query,'topic':'news','max_results':5,'include_answer':False})
        response.raise_for_status()
        data = response.json()
        return [{'title':r.get('title',''), 'url':r.get('url',''), 'date':r.get('published_date') or r.get('date'), 'content':r.get('content','')[:1200], 'source_id':r.get('url','')} for r in data.get('results',[])]
