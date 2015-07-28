from __future__ import print_function
from bs4 import BeautifulSoup
import argparse
import json
import os
import requests
import sys

class VideoInfo:
    def __init__(self, video_url, series_name, season, episode):
        self.video_url = video_url
        self.series_name = series_name
        self.season = season
        self.episode = episode

def get_video_id(player_url):
    url_parts = player_url.split(",")
    id = url_parts[-1].split(".")[0]
    return id

def get_info_url(player_url):
    video_id = get_video_id(player_url);
    info_url_template = "http://player.pl/api/?platform=ConnectedTV&terminal=Samsung&format=json&v=2.0&authKey=ba786b315508f0920eca1c34d65534cd&type=episode&id={0}&sort=newest&m=getItem&deviceScreenHeight=1080&deviceScreenWidth=1920"
    info_url = info_url_template.format(video_id)
    return info_url

def get_web_video_info(info_url):
    json_response = requests.get(info_url)
    video_info = json.loads(json_response.text)

    video_info = video_info["item"];
    video_contents = video_info["videos"]["main"]["video_content"]
    best_quality_video_page = [video["url"] for video in video_contents if video["profile_name"] == "Bardzo wysoka"][0]
        
    web_video_url = requests.get(best_quality_video_page)
    
    video_info = VideoInfo(web_video_url.text, 
                           video_info["serie_title"], 
                           int(video_info["season"]) + 1, 
                           int(video_info["episode"]))

    return video_info

#def get_next_episode_player_url(player_url):
#    player_page = requests.get(player_url)
#    soup = BeautifulSoup(player_page.text, 'html.parser')
#    next_episode_a = soup.select("div.nextEpisode a");
#    next_episode = next_episode_a[0].attrs["href"]

#    return "http://player.pl/" + next_episode

def get_next_episode_player_url(player_url):
    video_id = int(get_video_id(player_url)) + 1
    return "http://player.pl/seriale-online/kasia-i-tomek-odcinki,1/odcinek-{0},S00E{0:02},{0}.html".format(video_id)

def download_file(url, directory, file_name):
    local_filename = directory + file_name

    if not os.path.exists(directory):
        os.makedirs(directory)

    print("Downloading " + file_name, end="")

    # NOTE the stream=True parameter
    response = requests.get(url, stream=True)
    counter = 0

    with open(local_filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                counter += 1
                if counter % 1000 == 0: print(".", end="")

                file.write(chunk)
                file.flush()

    print(" DONE!")

    return local_filename

def download_video(initial_player_url, path, download_series):
    player_url = initial_player_url

    print("Downloading to " + path)

    while True:
        info_url = get_info_url(player_url)
        video_info = get_web_video_info(info_url)

        file_name = "{0} S{1:02}E{2:02}.avi".format(video_info.series_name, video_info.season, video_info.episode)
        season_path = path + "/{0}/Sezon {1:02}/".format(video_info.series_name, video_info.season)
        download_file(video_info.video_url, season_path, file_name)

        if not download_series:
            break;

        player_url = get_next_episode_player_url(player_url)

def get_args(argv):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('url', 
                        type=str, 
                        help='player.pl url')

    parser.add_argument('--series', 
                        action='store_true',
                        default=False,
                        help='downloads whole series')

    parser.add_argument('--path', 
                        type=str,
                        help='download path')

    args = parser.parse_args(argv)
    return args

def main(argv):
    arguments = get_args(argv)

    player_url = arguments.url
    download_series = arguments.series
    path = arguments.path

    download_video(player_url, path, download_series)
    
    print("SUCCESS!")


if __name__ == "__main__":
    main(sys.argv[1:])