import asyncio
import os

import aiohttp
import requests
import ujson as json
from multiprocessing import Pool
from main import parse_article
import dbm
import asyncio



def get_url_page(page=1):
    print(page)
    guardian_url = f'https://content.guardianapis.com/search?section=commentisfree&page-size=200&api-key={os.environ["guardian_api_key"]}&page={page}'
    return guardian_url


data = []
retries = []


def extend_data(results):
    try:
        data = results
        f = open('guardian_urls.json', 'w')
        f.write(json.dumps(results))
        f.close()

    except:
        print("Error at extend_data:", results)

def err_callback(results):
    print("Error at: ", results)

def fetch(url):
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json()['response']
    else:
        retries.append(url)
        return

    return response


def wrapper(i):
    return fetch(get_url_page(i))


def fetch_urls():
    num_pages = 190

    print("Total pages", num_pages)
    with Pool(processes=8) as pool:
        t = pool.map_async(wrapper, range(1, num_pages + 1), callback=extend_data, error_callback=err_callback)
        t.wait()


datadb = dbm.open('guardian.db', 'w')
processed_urls = set()

for key in datadb.keys():
    temp = json.loads(datadb[key])
    if "url" not in temp or "plain_text" not in temp:
        del datadb[key]
    else:
        processed_urls.add(json.loads(datadb[key])["url"])


async def download_urls():
    responselist = json.load(open('guardian_urls.json', 'r'))
    tasks = []
    async with aiohttp.ClientSession() as session:
        for response in responselist:
            for url in response['results']:
                if url["webUrl"] in processed_urls:
                    print("Already processed")
                    continue
                tasks.append(asyncio.create_task(parse_article(url["webUrl"], session, datadb)))

                if len(tasks) % 50 == 0:
                    await asyncio.sleep(10)
        await asyncio.gather(*tasks)

asyncio.run(download_urls())
