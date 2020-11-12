import requests
import json
import os
from PIL import Image

def get_data(api_key):
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}').text
    response = json.loads(raw_response)
    return response


def get_date(response):
    date = response['date']
    return date


def get_explaination(response):
    explaination = response['explanation']
    return explaination


def get_hdurl(response):
    hdurl = response['hdurl']
    return hdurl


def get_media_type(response):
    media_type = response['media_type']
    return media_type

def get_service_version(response): 
    service_version = response['service_version']
    return service_version


def get_title(response):
    service_version = response['title']
    return service_version

def get_url(response):
    url = response['url']
    return url

def download_image(url, date):
    if os.path.isfile(f'{date}.png') == False:
        raw_image = requests.get(url).content
        with open(f'{date}.jpg', 'wb') as file:
            file.write(raw_image)
            
    else:
        return FileExistsError


def convert_image(image_path):
    path_to_image = os.path.normpath(image_path)

    basename = os.path.basename(path_to_image)

    filename_no_extension = basename.split(".")[0]

    base_directory = os.path.dirname(path_to_image)

    image = Image.open(path_to_image)
    image.save(f"{base_directory}/{filename_no_extension}.png")
