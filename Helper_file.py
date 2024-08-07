import time
import threading
import logging
from dotenv import load_dotenv
import os
import base64
from requests import post
import json
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
        

def add_to_db(data_to_insert, type):
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
        elif type == 'similar':
            insert_query = "INSERT INTO similar_artist (artist, artist_id, ranks, similar_a, sim_ID) VALUES (%s, %s, %s, %s, %s)"
        else:
            print("Type Not available")
        
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        print(cursor.rowcount, "record(s) inserted successfully.")
    except mysql.connector.Error as error:
        print(f"Error inserting data into MySQL table: {error}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn is not None:
            conn.close()
        
def text_file(input_file, output_file,type):
    try:
        with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
            for line in fin:
                modified_line = line.replace(' ', '%20')
                fout.write(modified_line)

        with open(output_file, 'r') as file:
            artists_search = [line.strip() for line in file.readlines()]
        with open(input_file, 'r') as file:
            artists_display = [line.strip() for line in file.readlines()]

        if type == "search":
            return artists_search
        elif type == "display":
            return artists_display   
    
    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found.")
        return []