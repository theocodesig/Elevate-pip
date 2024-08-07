import json
import threading
from requests import get
import time
from Helper_file import TokenCache,add_to_db,text_file


def process_artist(token, artist, limit=5):
    url = "https://api.spotify.com/v1/artists/{id}/related-artists"
    headers = {"Authorization": f"Bearer {token}"}
    artist_id = get_artist_id_by_name(token, artist)
    artist_disp = artist_display.pop()
    print(artist)
    if artist_id:
        query_url = url.format(id=artist_id)
        result = get(query_url, headers=headers)
        json_result = json.loads(result.content)
        print(f"Related artists for {artist}:")
        related_artists = json_result['artists']
        data_to_insert = []
        for i, related_artist in enumerate(related_artists):
            if i >= limit:
                break
            similar_artist_name = related_artist['name']
            similar_artist_id = related_artist['id']
            data_to_insert.append((artist_disp, artist_id, i + 1, similar_artist_name, similar_artist_id))
            
            print(similar_artist_name)

        add_to_db(data_to_insert, "similar")



def get_artist_id_by_name(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    query = f"q={artist_name}&type=artist"

    query_url = f"{url}?{query}"
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)
    artists = json_result.get("artists", {}).get("items", [])
    if artists:
        return artists[0]['id']
    return None


# Example usage
token_cache = TokenCache(ttl=3600)

def refresh_token_periodically():
    while True:
        token_cache.get_token()
        time.sleep(3600)  # Refresh every hour


threading.Thread(target=refresh_token_periodically, daemon=True).start()

input_file = 'artists_input.txt'
output_file = 'artists_out.txt'

artist_search = text_file(input_file,output_file,"search")
artist_display = text_file(input_file,output_file,"display")

def similar_artists():
    while True:
        token = token_cache.get_token()
        term = artist_search.pop()
        process_artist(token, term)
        time.sleep(1)