import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
import os

headers = {'User-agent': 'Mozilla/5.0'}
cookies = {'birthtime': '283993201', 'mature_content': '1'}
load_dotenv()

connection_string = os.getenv("CONN_STRING")
client = MongoClient(connection_string)


def fetch_info(app_id):
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&lang=en"
    store_url = f"https://store.steampowered.com/app/{app_id}/"

    api_response = requests.get(url=api_url, headers=headers)
    if api_response.json()[str(app_id)]["success"] is False:
        return False
    data = api_response.json()[str(app_id)]["data"]

    # Skipping if it is a DLC
    if data["steam_appid"] != app_id:
        print(data["steam_appid"], app_id)
        return False

    # Skipping if it is a DLC
    if data["type"] != "game":
        return False

    name = data["name"]

    # About me section + Cleaning
    description = data["about_the_game"]
    description = re.sub(r'<[^>]*>', " ", description)
    description = description.replace("\n", " ")
    description = description.strip()

    # Game tags
    store_response = requests.get(url=store_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(store_response.content, "html.parser")
    tags = [i.text.strip() for i in soup.find_all("a", {"class": "app_tag"})]
    tags = tags[:5] if len(tags) > 5 else tags
    tags = ' '.join(tags)

    time.sleep(2)
    return name, description, tags


def extraction_loop(ids, numbers=None):
    counter = 0
    game_data = list()
    for app_id in ids:
        data = fetch_info(app_id)
        if data:
            game_data.append({"app_id": app_id, "name": data[0], "description": data[1], "tags": data[2]})
            if counter % 50 == 0:
                print(counter)
            # Remove this block after testing on first 500
            if numbers:
                if counter > numbers:
                    break
                counter += 1

    df = pd.DataFrame(game_data)
    # df.to_csv("game_data.csv", index=False)
    df_records = df.to_dict(orient='records')
    collection = client.SteamerDB.GameData
    collection.insert_many(df_records)


def fetch_ids():
    url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json"
    response = requests.get(url)
    data = response.json()["applist"]["apps"]
    app_ids = [i["appid"] for i in data]
    return app_ids


def reset_game_database():
    collection = client.SteamerDB.GameData
    result = collection.delete_many({})
    return f"{result.deleted_count} documents deleted from the collection."
