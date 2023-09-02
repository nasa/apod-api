import requests
import json
import os
from PIL import Image


def get_copyright(response):
    return response['copyright']


def get_data(api_key):
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}').text
    response = json.loads(raw_response)
    return response


def get_date(response):
    return response['date']


def get_explanation(response):
    return response['explanation']


def get_hdurl(response):
    return response['hdurl']


def get_media_type(response):
    return response['media_type']


def get_service_version(response): 
    return response['service_version']


def get_title(response):
    return response['title']


def get_url(response):
    return response['url']

def download_image(url, date):
    if not os.path.isfile(f'{date}.png'):
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
