from Helper_file import TokenCache,add_to_db,text_file
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import logging
from requests import get

def save_to_csv(data_to_insert, type):
    filename = f"{type}_data.csv"
    header = []

    if type == 'album':
        header = ['term', 'ranks', 'name', 'upc', 'id', 'artist', 'Total_Tracks']
    elif type == 'artist':
        header = ['term', 'ranks', 'name', 'id', 'genres', 'followers', 'popularity']
    elif type == 'track':
        header = ['term', 'ranks', 'name', 'isrc', 'id', 'artist', 'album', 'release_date', 'popularity']

    # Check if the file exists and has data
    file_exists = False
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            if next(reader, None):
                file_exists = True
    except FileNotFoundError:
        pass

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(header)
        writer.writerows(data_to_insert)

input_file = 'input.txt'
output_file = 'output.txt'

def get_album_upc(album_id, token):
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    headers = {"Authorization": f"Bearer {token}"}

    result = get(url, headers=headers)
    
    if result.status_code == 200:
        album_info = result.json()
        upc = album_info.get("external_ids", {}).get("upc")
        return upc
    else:
        logging.error("Failed to retrieve album details: %s", result.content)
        return None

def search_spotify(token, query, search_type, limit=5):
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    query_params = {
        "q": query,
        "type": search_type,    
        "limit": limit
    }
    disp_name=raw_list.pop()
    result = get(url, headers=headers, params=query_params)
    
    if result.status_code == 200:
        
        json_result = result.json()
        
        if search_type == "track":
            
            items = json_result.get("tracks", {}).get("items", [])
            
            for idx, item in enumerate(items, start=1):
                
                
                artists = ', '.join([artist["name"] for artist in item["artists"]])
                album_name = item["album"]["name"]
                release_date = item["album"]["release_date"]
                popularity = item["popularity"]
                preview_url = item["preview_url"]
                isrc = item.get("external_ids", {}).get("isrc") if item.get("external_ids") else None
                track_id = item["id"]
                
                
                data_to_insert = [(disp_name, idx, item['name'], isrc, track_id, artists, album_name, release_date, popularity)]
                add_to_db(data_to_insert, search_type)
                save_to_csv(data_to_insert,search_type)


                print(f"Track {idx}: {item['name']}")
                print(f"Artists: {artists}")
                print(f"Album: {album_name}")
                print(f"Release Date: {release_date}")
                print(f"Popularity: {popularity}")
                print(f"Preview URL: {preview_url}")
                print(f"Track ID: {track_id}")
                if isrc:
                    print(f"ISRC: {isrc}")
                print()

        elif search_type == "album":
           
            items = json_result.get("albums", {}).get("items", [])
           
            for idx, item in enumerate(items, start=1):
           
                artists = ', '.join([artist["name"] for artist in item["artists"]])
                release_date = item["release_date"]
                total_tracks = item["total_tracks"]
                upc = item.get("external_ids", {}).get("upc") if "external_ids" in item else None
                album_id = item["id"]
                upc = get_album_upc(album_id, token)
                data_to_insert = [(disp_name, idx, item['name'], upc, album_id, artists, total_tracks)]
           
           
                add_to_db(data_to_insert, search_type)
                save_to_csv(data_to_insert,search_type)


                print(f"Album {idx}: {item['name']}")
                print(f"Album ID: {album_id}")
                print(f"Artists: {artists}")
                print(f"Release Date: {release_date}")
                print(f"Total Tracks: {total_tracks}")
                if upc:
                    print(f"UPC: {upc}")
                print()

        elif search_type == "artist":
            
            items = json_result.get("artists", {}).get("items", [])
            
            for idx, item in enumerate(items, start=1):
            
                genres = ', '.join(item.get("genres", [])) if item.get("genres") else "Unknown"
                followers = item["followers"]["total"] if "followers" in item else "Unknown"
                popularity = item["popularity"] if "popularity" in item else "Unknown"
                artist_id = item["id"]
                data_to_insert = [(disp_name, idx, item['name'], artist_id, genres, followers, popularity)]
            
            
                add_to_db(data_to_insert, search_type)
                save_to_csv(data_to_insert,search_type)

                print(f"Artist {idx}: {item['name']}")
                print(f"Genres: {genres}")
                print(f"Artist Id: {artist_id}")
                print(f"Followers: {followers}")
                print(f"Popularity: {popularity}")
                print()

    else:
        logging.error("Search failed: %s", result.content)


token_cache = TokenCache(ttl=3600)

def refresh_token_periodically():
    while True:
        token_cache.get_token()
        time.sleep(3600)

threading.Thread(target=refresh_token_periodically, daemon=True).start()



lines_list = text_file(input_file, output_file,"search")
raw_list = text_file(input_file, output_file,"display")



def search_all_types(token, term):
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(search_spotify, token, term, "track")
        executor.submit(search_spotify, token, term, "artist")
        executor.submit(search_spotify, token, term, "album")

while True:
    token = token_cache.get_token()
    if lines_list:
        term = lines_list.pop()
        search_all_types(token, term)
        time.sleep(5)
    else:
        break