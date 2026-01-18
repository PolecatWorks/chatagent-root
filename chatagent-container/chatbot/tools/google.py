import logging

logger = logging.getLogger(__name__)


import requests


def google_search(query, api_key, cse_id, num=5):
    """
    Search Google using the Custom Search JSON API.

    Args:
        query (str): Search query.
        api_key (str): Google API key.
        cse_id (str): Custom Search Engine ID.
        num (int): Number of results to return (max 10 per request).

    Returns:
        list: List of search result dicts with 'title', 'link', and 'snippet'.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = []
    data = response.json()
    for item in data.get("items", []):
        results.append(
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            }
        )
    return results


# Example usage:
# api_key = "YOUR_GOOGLE_API_KEY"
# cse_id = "YOUR_CUSTOM_SEARCH_ENGINE_ID"
# results = google_search("python programming", api_key, cse_id)
# for r in results:
#     print(r["title"], r["link"])
