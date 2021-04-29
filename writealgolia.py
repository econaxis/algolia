import ujson as json
import dbm
from algoliasearch.search_client import SearchClient
from algoliasearch.configs import SearchConfig
import os

from main import custom_filters

config = SearchConfig("WDX3IWJU87", os.environ['algolia_key'])
config.batch_size = 100
client = SearchClient.create_with_config(config)
index = client.init_index('main')
index.set_settings({'attributeForDistinct': 'title', 'advancedSyntax': True})
db = dbm.open('master.db', 'w')
added = dbm.open('added.db', 'c')

objtoadd = []
keysadded = []
for key in db.keys():
    curlen = 0
    if key not in added:
        if key.decode('utf-8')[0:4].isnumeric():
            continue
        article = json.loads(db[key])
        if (not article["title"]):
            continue
        custom_filters(article)

        i = 0
        while i < len(article["plain_text"]):
            article["plain_text"][i] = article["plain_text"][i]["text"]

            if len(article["plain_text"][i]) < 30:
                article["plain_text"].pop(i)
                continue

            curlen += len(article["plain_text"][i])

            if "plain_content" in article: article.pop("plain_content")
            if "content" in article: article.pop("content")

            if curlen > 9400 and i < len(article["plain_text"]) - 1:
                next_dict = article.copy()
                next_dict["plain_text"] = article["plain_text"][i + 1:]
                article["plain_text"] = article["plain_text"][0: i + 1]
                db[str(key) + f"({int(curlen / 8000)})"] = json.dumps(next_dict)
                break
            i += 1

        # Add objectid to article object
        article["objectID"] = abs(hash(article["url" if "url" in article else "title"]))
        keysadded.append(key)
        objtoadd.append(article)

    if len(objtoadd) >= 100:
        print('Pushing')
        index.save_objects(objtoadd, {'autoGenerateObjectIDIfNotExist': False})
        for a in keysadded:
            added[a] = "1"
        keysadded.clear()
        objtoadd.clear()
