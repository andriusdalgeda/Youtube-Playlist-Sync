# facilitates download of youtube video
# pip install pytube3 - https://pastebin.com/Ak7qE6nV (KeyError: 'cipher')
from pytube import YouTube

# converts mp4 file from pytube to mp3
# pip install moviepy
from moviepy.editor import *

# create a credentials.py file
from credentials import Youtube_API_Key, Playlist_ID, AWS_Key, AWS_Secret_Key, AWS_Region, AWS_Bucket

# used to authenticate and upload to s3 aws storage
# pip install boto3
import logging
import boto3

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

                    video_stream = video.streams.first()

                    print('Downloading',video_title + '...')

                    start = time.time()

                    video_stream.download()

                    # appends id to csv to ensure the video is not downloaded again
                    file.write(video_id + ',')

                    # Confirms that the video was downloaded and displays the time taken
                    print('Completed download of', video_title + '\n' + 'The download took',time.time()-start,'seconds'+'\n')

                    # replaces | to stop error occuring - error with moviepy module
                    video_convert = video_title.replace('|', '') + '.mp4'
                    video_convert_mp3 = video_convert.replace('mp4', 'mp3')
                    video = VideoFileClip(video_convert)
                    video.audio.write_audiofile(video_convert_mp3)
                    video.close()

                    # removes mp4 version
                    os.remove(video_convert)
                
                    def upload_to_aws(local_file, bucket, s3_file):

                        key = AWS_Key
                        secret_key = AWS_Secret_Key
                        region = AWS_Region

                        s3 = boto3.client('s3', aws_access_key_id=key,
                                        aws_secret_access_key=secret_key)

                        try:
                            s3.upload_file(local_file, bucket, s3_file)
                            print("Upload Successful")
                            return True
                        except FileNotFoundError:
                            print("The file was not found")
                            return False
                        except NoCredentialsError:
                            print("Credentials not available")
                            return False

                    uploaded = upload_to_aws(video_convert_mp3 , AWS_Bucket, video_convert_mp3)

                    # removes mp3 version after upload
                    os.remove(video_convert_mp3)
                
            file.close()
            # Waits 60 seconds before checking for changes within the playlist
            time.sleep(60)
            
            main()

if __name__ == "__main__":
    main()