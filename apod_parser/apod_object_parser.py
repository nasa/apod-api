import requests
import json
import os
from PIL import Image

def get_data(api_key):
    raw_response = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={api_key}').text # scraping APOD info from API
    #print(raw_response)
    response = json.loads(raw_response) # converting text file to JSON
    return response


def get_date(response):
    date = response['date'] # getting date from JSON dict
    return date


def get_explaination(response):
    explaination = response['explanation'] # getting explanation from JSON dict
    return explaination


def get_hdurl(response):
    hdurl = response['hdurl'] # getting hdurl from JSON dict
    return hdurl


def get_media_type(response):
    media_type = response['media_type'] # getting media type from JSON dict
    return media_type

def get_service_version(response): 
    service_version = response['service_version'] # getting service version from JSON dict
    return service_version


def get_title(response):
    service_version = response['title'] # getting title from JSON dict
    return service_version

def get_url(response):
    url = response['url'] # getting url from JSON dict
    return url

def download_image(url, date):
    if os.path.isfile(f'{date}.png') == False:
        raw_image = requests.get(url).content # scraping image from url
        with open(f'{date}.jpg', 'wb') as file: # opening file
            file.write(raw_image) # writing in scraped image into jpg
            
    else:
        return FileExistsError 


def convert_image(image_path):
    path_to_image = os.path.normpath(image_path) # normalizing path of image

    basename = os.path.basename(path_to_image) # extracting basename from image

    filename_no_extension = basename.split(".")[0] # splitting filename to remove type

    base_directory = os.path.dirname(path_to_image) # getting image directory 

    image = Image.open(path_to_image) # opening file
    image.save(f"{base_directory}/{filename_no_extension}.png") # resaving image as png

#get_data('cnaoQOLrIXQG50zk4zLA9fz5ywAg6FRZMcAs346a')
