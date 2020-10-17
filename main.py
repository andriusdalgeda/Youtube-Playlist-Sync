# facilitates download of youtube video
# pip install pytube3 - https://pastebin.com/Ak7qE6nV (KeyError: 'cipher')
from pytube import YouTube

# converts mp4 file from pytube to mp3
# pip install moviepy
from moviepy.editor import *

# create a credentials.py file
from credentials import *

# used to authenticate and upload to mega.nz cloud storage
# pip install mega
from mega import Mega

# YoutubeDataAPI authentication
# pip install --upgrade google-api-python-client
import googleapiclient.discovery

import string
import time
import os

def main():
    while True:
        # oauth disabled for personal use
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        # Logs into mega.nz and creates a folder if not present
        mega = Mega()
        m = mega.login(MegaUsername, MegaPassword)
        m.create_folder('Music')

        with open('video-id.csv','a+') as file:
            
            # resets file read position
            file.seek(0)

            file_read = file.read()

            api_service_name = "youtube"
            api_version = "v3"
            DEVELOPER_KEY = Youtube_API_Key

            youtube = googleapiclient.discovery.build(
                api_service_name, api_version, developerKey = DEVELOPER_KEY)

            # forms the request url - defines the needed info within the json response (part='') as default is not sufficient for this use-case
            request = youtube.playlistItems().list(
                maxResults=100,
                playlistId=Playlist_ID,
                part="snippet,contentDetails"
            )
            videos = request.execute()

            for video in videos["items"]:
                video_id = video["contentDetails"]["videoId"]

                if video_id in file_read:
                    pass
                
                elif video_id not in file_read:
                    # converts the videoID to a link shich can be used by pytube module
                    video_url = "https://www.youtube.com/watch?v=" + video_id

                    # defines url for the pytube module
                    video = YouTube(video_url)

                    video_title = video.title.replace('.', '')

                    video_stream = video.streams.filter(subtype='mp4').first()

                    video_stream.download()

                    # appends id to csv to ensure the video is not downloaded again
                    file.write(video_id + ',')

                    # removes certain characters from video title to limit errors - errors with moviepy
                    blacklisted_chars = ['|', '#']

                    for i in blacklisted_chars:
                        video_title = video_title.replace(i, '')

                    video_convert = video_title+'.mp4'

                    # Confirms that the video was downloaded and displays the time taken
                    print('Completed download of', video_convert + '\n')

                    # renames and converts mp4 into mp3 format
                    video_mp3 = video_convert.replace('.mp4', '.mp3')
                    video = VideoFileClip(video_convert)
                    video.audio.write_audiofile(video_mp3)
                    video.close()

                    # removes mp4 version
                    os.remove(video_convert)
                    
                    # upload to mega.nz storage in defined folder
                    folder = m.find('Music')
                    m.upload(video_mp3, folder[0])

                    # removes mp3 version after upload
                    os.remove(video_mp3)

            # closes file to ensure appends are saved
            file.close()
            # Waits 60 seconds before checking for changes within the playlist
            time.sleep(60)
            
            main()

if __name__ == "__main__":
    main()