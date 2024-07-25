import os
import base64
import json
import threading
from requests import post, get
from dotenv import load_dotenv
import time
import logging
import mysql.connector

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

logging.basicConfig(level=logging.INFO)




class TokenCache:
    def __init__(self, ttl):
        self.token = None
        self.expiration = 0
        self.ttl = ttl
        self.lock = threading.Lock()

    def get_token(self):
        with self.lock:
            if self.token is None or time.time() >= self.expiration:
                self.token = self.refresh_token()
                self.expiration = time.time() + self.ttl
            return self.token

    def refresh_token(self):
        auth_string = client_id + ":" + client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)
        
        if result.status_code == 200:
            json_result = json.loads(result.content)
            return json_result["access_token"]
        else:
            logging.error("Failed to get token: %s", result.content)
            raise Exception("Failed to get token")

def process_file(input_file, output_file):
    try:
        with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
            for line in fin:
                modified_line = line.replace(' ', '%20')
                fout.write(modified_line)

        with open(output_file, 'r') as file:
            lines_list = [line.strip() for line in file.readlines()]
        
        return lines_list
    
    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found.")
        return []

input_file = 'input.txt'
output_file = 'output.txt'


def add_to_db(data_to_insert,type):
    try:
        conn = mysql.connector.connect(
            host = "***REMOVED_DATABASE_HOST***",
            database = "***REMOVED_DATABASE_NAME***",
            user = "***REMOVED_DATABASE_USERNAME***",
            password = "***REMOVED_DATABASE_PASSWORD***"
        )
        cursor = conn.cursor()
        
        if type == 'album':
            insert_query = "INSERT INTO album (term,ranks,name,upc,id,artist,Total_Tracks) VALUES (%s, %s, %s, %s, %s, %s,%s)"
        elif type == 'artist':
            insert_query = "INSERT INTO artist (term,ranks,name,id,genres,followers,popularity) VALUES (%s, %s, %s, %s, %s, %s,%s)"
        elif type == 'track':
            insert_query = "INSERT INTO track (term,ranks,name,isrc,id,artist,album,release_date,popularity) VALUES (%s, %s, %s, %s, %s, %s,%s,%s,%s)"
        else:
            print("Type Not available")
        
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        print(cursor.rowcount, "record(s) inserted successfully for insert_data_2.")
    except mysql.connector.Error as error:
        print(f"Error inserting data into MySQL table: {error}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None:
            conn.close()

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
                track_id = item["id"]  # Accessing the ID of the track
#term,ranks,name,isrc,id,artist,album,release_date,popularity
                data_to_insert = [(query,idx,item['name'],isrc,track_id,artists,album_name,release_date,popularity)]
                #add_to_track(data_to_insert)
                add_to_db(data_to_insert,search_type)
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
                album_id = item["id"]  # Accessing the ID of the album
                upc = get_album_upc(album_id, token)
                #term,ranks,name,upc,id,artist,Total_Tracks
                data_to_insert = [(query,idx,item['name'],upc,album_id,artists,total_tracks)]
                #add_to_album(data_to_insert)
                add_to_db(data_to_insert,search_type)

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
                #term,ranks,name,id,genres,followers,popularity
                data_to_insert = [(query,idx,item['name'],artist_id,genres,followers,popularity)]
                # add_to_artist(data_to_insert)
                add_to_db(data_to_insert,search_type)

                print(f"Artist {idx}: {item['name']}")
                print(f"Genres: {genres}")
                print(f"Artist Id: {artist_id}")
                print(f"Followers: {followers}")
                print(f"Popularity: {popularity}")
                print()                 

  

    else:
        logging.error("Search failed: %s", result.content)

# Example usage
token_cache = TokenCache(ttl=3600)

def refresh_token_periodically():
    while True:
        token_cache.get_token()
        time.sleep(3600)  # Refresh every hour

threading.Thread(target=refresh_token_periodically, daemon=True).start()

lines_list = process_file(input_file, output_file)

while True:
    
    token = token_cache.get_token()
    term = lines_list.pop()
    search_spotify(token, term, search_type="track")
    search_spotify(token, term, search_type="artist")
    search_spotify(token, term, search_type="album")
    
    time.sleep(5)
