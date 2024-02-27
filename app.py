from warnings import catch_warnings
from flask import Flask, render_template, request, redirect, url_for, jsonify
from ytmusicapi import YTMusic
import subprocess
import json
import sys
import os

#Initialize Flask as the object app
app = Flask(__name__)

#Initialize ytmusic unofficial API
ytmusic = YTMusic("oauth.json")


persistent_url_list = []
album_information = []
albums_value=None
album_items = []


@app.route('/')
def index():

    return render_template('index.html')
    
@app.route('/search', methods=['POST'])
def search():
    #clear url list before next search
    album_items.clear()
    album_information.clear()
    persistent_url_list.clear()
    
    # Pass the search query to YTMusic API
    search_query = request.form['search_query']
    search_results = ytmusic.search(search_query, limit=20)

    print("SEARCH RESULTS IS THE TYPE: ", type(search_results))

    # Check if search_results is not empty
    if search_results:

        #print("DEBUG: ", json.dumps(search_results, indent=2))

        for dict_entry in search_results:

            if "artists" in dict_entry:

                if dict_entry["artists"]:

                    artist_info = dict_entry["artists"][0]
                    name = artist_info["name"]
                    id   = artist_info["id"]
                    print(f"ARTIST NAME = {name}")
                    print(f"ARTIST ID   = {id}")

                else:
                    print(f"ARTIST NAME = None")
                    print(f"ARTIST ID = None")

                if id:
                    channel_info = ytmusic.get_artist(id)
                    #print("ARTIST_INFORMATION = ", json.dumps(channel_info, indent=4))

                    if "channelId" in channel_info:
                        channelId = channel_info["channelId"]
                        print(f"ARTIST CHANNEL ID = {channelId}")
                    else:
                        print("ChannelId not found in channel_info")

                    # Check if "params" key exists in "albums" or "singles"
                    if "albums" in channel_info:
                        if "browseId" and "params" in channel_info["albums"]:
                            print("RELEVENT BROWSEID = ", channel_info["albums"]["browseId"])
                            print("RELEVENT PARAMS = ", channel_info["albums"]["params"])

                            all_artist_albums = ytmusic.get_artist_albums(channel_info["albums"]["browseId"], channel_info["albums"]["params"])
                            album_number = 0
                            item_titles = []
                            item_browseids = []
                            for item in all_artist_albums:
                                album_number+=1
                                print("Album ", album_number)
                                print("TITLE = ", item["title"])
                                item_titles.append(item["title"])
                                print("browseId = ", item["browseId"])
                                item_browseids.append(item["browseId"])
                            
                            #print("ALL ARTIST ALBUMS = ", json.dumps(all_artist_albums, indent = 1))

                            for item in item_browseids:
                                album_items.append(ytmusic.get_album(item))
                            
                            #print("ALBUM INFORMATION = ", json.dumps(album_items, indent = 2))
                            
                            video_id_items = []
                            for item in album_items:
                                for track in item["tracks"]:
                                    video_id_items.append(track["videoId"])
                            #print("VIDEO IDS = ", video_id_items)
                            break
                        else:
                            print("COMBINATION OF BOTH BROWSEID AND PARAMS KEYWORDS NOT FOUND")   
                            print("albums type = ", type(channel_info["albums"]))
                            albums_value = channel_info["albums"]
                            print("Albums parameter found.")    
                            break
                    else: 
                        print("ALBUMS KEYWORD NOT FOUND")
                        sys.exit(0)
                else:
                    print("NO IDS FOUND FOR ARTIST")
                    sys.exit(0)
    else:
        print("No search results found.")


    if album_items:
        for album in album_items:
            largest_dimension = 0
            album_urls = []  # Initialize album_urls for each album

            if "thumbnails" in album:
                for thumbnail in album["thumbnails"]:
                    dimension = thumbnail["width"] * thumbnail["height"]
                    
                    if dimension > largest_dimension:
                        album_urls.clear()
                        album_urls.append(thumbnail["url"])
                        largest_dimension = dimension
                
                if album_urls:  # Only append if album_urls is not empty
                    persistent_url_list.extend(album_urls)
            else:
                print("NO THUMBNAILS FOUND IN ALBUM")

        print("all URLS = ", json.dumps(persistent_url_list, indent=4))
        return render_template('results.html', urls=persistent_url_list)

    else:
        albums_results = albums_value["results"]
        album_ids = []
        print("DEBUG ALBUMS RESULTS = ", album_items)
        

        for album in albums_results:
            # Accessing individual properties of the album
            title = album["title"]
            year = album["year"]
            browseId = album["browseId"]
            thumbnails = album["thumbnails"]
            isExplicit = album["isExplicit"]

            album_ids.append(browseId)
        print("DEBUG ALBUM IDS = ", album_ids)
        for item in album_ids:
            album = ytmusic.get_album(item)
            album_information.append(album)
        print("ALBUM INFORMATION = ", album_ids)
        for album in album_information:
            largest_dimension = 0
            album_urls = []  # Initialize album_urls for each album

            if "thumbnails" in album:
                for thumbnail in album["thumbnails"]:
                    dimension = thumbnail["width"] * thumbnail["height"]
                    if dimension > largest_dimension:
                        album_urls.clear()
                        album_urls.append(thumbnail["url"])
                        largest_dimension = dimension
            
            if album_urls:  # Only append if album_urls is not empty
                persistent_url_list.extend(album_urls)

        #print("all URLS = ", json.dumps(persistent_url_list, indent=4))
        return render_template('results.html', urls=persistent_url_list)        
    
@app.route('/handle_thumbnail_url', methods=['POST'])
def handle_thumbnail_url():
    thumbnail_url = request.json['thumbnail_url']
    # Process the thumbnail URL as needed

    # if user clicked album, look through list of dicts for specific url
    # if that dict has that specific url, look through that dict for ["tracks"]["videoIds"]
    # append all videoIds to a list and yt-dlp each item in that list with the videoId appended to the end
   
    album_video_ids = []
    #print("DEBUG ALBUM INFORMATION INFO = ", json.dumps(album_information, indent=4))
    if album_items:
        for album in album_items:
            if "thumbnails" in album:
                for element in album["thumbnails"]:
                    if "url" in element:
                        if element["url"] == thumbnail_url:
                            print("URL MATCH FOUND")
                            if "tracks" in album:
                                print("album confirmed has tracks")
                                for item in album["tracks"]:
                                    #print("DEBUG INFO IN ALBUM[TRAKKKS = ", json.dumps(item, indent=4))
                                    if "videoId" in item:
                                        print("DEBUG I FIND VIDEO ID")
                                        album_video_ids.append(item["videoId"])
                            if "title" in album:
                                album_title = album["title"]
                            if "artists" in album:
                                print("DEBUG ARTIST CONFIRMED IN ALBUM")
                                for artist_element in album["artists"]:
                                    if "name" in artist_element:
                                        print("DEBUG NAME CONFIRMED IN ARTIST_ELEMENT")
                                        artist_name = artist_element["name"]
    else:
        for album in album_information:
            if "thumbnails" in album:
                for element in album["thumbnails"]:
                    if "url" in element:
                        if element["url"] == thumbnail_url:
                            print("URL MATCH FOUND")
                            if "tracks" in album:
                                print("album confirmed has tracks")
                                for item in album["tracks"]:
                                    #print("DEBUG INFO IN ALBUM[TRAKKKS = ", json.dumps(item, indent=4))
                                    if "videoId" in item:
                                        print("DEBUG I FIND VIDEO ID")
                                        album_video_ids.append(item["videoId"])
                            if "title" in album:
                                album_title = album["title"]
                            if "artists" in album:
                                print("DEBUG ARTIST CONFIRMED IN ALBUM")
                                for artist_element in album["artists"]:
                                    if "name" in artist_element:
                                        print("DEBUG NAME CONFIRMED IN ARTIST_ELEMENT")
                                        artist_name = artist_element["name"]

    # return f'Search results for: {query}'
    print("Tracks in this album = ", album_video_ids)

    base_dir = "/app/jellyfin_media/music"

    artist_dir = os.path.join(base_dir, artist_name)
    artist_album_dir = os.path.join(artist_dir, album_title)

    if not os.path.exists(artist_dir):
        os.makedirs(artist_dir)

    if not os.path.exists(artist_album_dir):
        os.makedirs(artist_album_dir)    

    output_location = os.path.join(artist_album_dir, "%(title)s.%(ext)s")
    #subprocess_command = ["python3", "/usr/local/bin/yt-dlp", f"https://www.youtube.com/watch?v={track}", "--extract-audio", "--audio-format", "best", "--embed-thumbnail", "--write-thumbnail", "--add-metadata", "-o", output_location]
    for item in album_video_ids:
        subprocess.run(["python3", "/usr/local/bin/yt-dlp", f"https://www.youtube.com/watch?v={item}", "--extract-audio", "--audio-format", "best", "--embed-thumbnail", "--write-thumbnail", "--add-metadata", "-o", output_location])
         
    #clear url list before next search
    album_items.clear()
    album_information.clear()
    persistent_url_list.clear()
    return render_template('downloading.html', thumbnail_url=thumbnail_url)
    
if __name__ == '__main__':
    app.run(debug=True)
