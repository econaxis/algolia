import aiohttp
import sys
from readabilipy.readabilipy import simple_json_from_html_string
import asyncio
import os
import ujson as json
import dbm

db = None
masterdb = None
nytimes_archive_url = None
timeout = aiohttp.ClientTimeout(total=30)


def custom_filters(articleobj):
    unwanted = set(["Credit...", "Image"])
    for t in range(len(articleobj["plain_text"])):
        if t >= len(articleobj["plain_text"]):
            continue
        if (articleobj["plain_text"][t]["text"] in unwanted):
            unwanted.add(articleobj["plain_text"][t]["text"])
            articleobj["plain_text"].pop(t)


articles = []
headlines = {}

# proxy_blacklist = {}

retrylist = []


# def blacklist(proxy):
#     if proxy in proxy_blacklist:
#         proxy_blacklist[proxy] += 1
#
#         if proxy_blacklist[proxy] > 3 and proxy in proxylist:
#             proxylist.remove(proxy)
#             proxy_blacklist.pop(proxy)
#     else:
#         proxy_blacklist[proxy] = 1

async def retry_request(url, session, num_retries=5):
    while num_retries:
        num_retries -= 1
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print("Response not 200, ", await response.text())
                    raise RuntimeError("request error", await response.text())
        except Exception as e:
            print("Error: ", e)
            await asyncio.sleep(30)
    return -1

parsesem = asyncio.Semaphore(20)
async def parse_article(url, session, db, return_article = False):
    print("Parsing ", url)
    aurl = url.replace("https://", "http://")
    async with parsesem:
        resp_text = await retry_request(aurl, session)
    if resp_text == -1: return  # Error code

    article = simple_json_from_html_string(resp_text, use_readability=True)

    article.pop('content')
    article.pop('plain_content')
    article["url"] = url

    if url in headlines:
        dbkey = headlines[url]
    else:
        dbkey = article["title"]

    db[dbkey] = json.dumps(article)
    print(dbkey, f" pushed to DB")

    if return_article:
        return article


async def get_nytimes_urls(year, month):
    async with aiohttp.ClientSession(timeout=timeout) as session:
        print("Starting ", year, month)
        async with session.get(nytimes_archive_url.format(year=year, month=month), timeout=20) as response:
            print("Received NYTimes API response")
            if response.status != 200:
                raise RuntimeError("Response: ", await response.text())
            try:
                data = await response.json()
            except asyncio.TimeoutError:
                return
            data = data["response"]["docs"]
        db[f"{year}-{month}"] = json.dumps(data)

        download_tasks = []
        for article in data:
            if article["headline"]["main"] in db or article["headline"]["main"] in masterdb:
                continue
            url = article['web_url']
            headlines[url] = article["headline"]["main"]
            download_tasks.append(asyncio.create_task(parse_article(url, session, db)))
            await asyncio.sleep(2)

        await asyncio.gather(*download_tasks)


async def start_tasks():
    tasks = []
    for month in range(1, 13):
        tasks.append(asyncio.create_task(get_nytimes_urls(int(sys.argv[1]), month)))
        await asyncio.sleep(200)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    db = dbm.open(f'/home/henry/articles{sys.argv[1]}.db', 'c')
    masterdb = dbm.open('master.db', 'r')
    API_KEY = os.environ["nytimes_api_key"]
    nytimes_archive_url = 'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json' + f'?api-key={API_KEY}'
    asyncio.run(start_tasks())
