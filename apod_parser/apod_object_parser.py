import json
import os

import requests
from PIL import Image


def get_data(api_key):
    from datetime import date

    use_date = date.today().strftime("%y%m%d")
    raw_response = requests.get(
        f"https://science.nasa.gov/wp-json/wp/v2/apod-basic/?api_key={api_key}"
    ).text
    response = json.loads(raw_response)[0]
    return response


def get_alt(response):
    alt = response["alt"]
    return alt


def get_basic_html(response):
    basic_html = response["basic_html"]
    return basic_html


def get_basic_html_url(response):
    basic_html_url = response["basic_html_url"]
    return basic_html_url


def get_copyright(response):
    copyright = response["copyright"]
    return copyright


def get_credit(response):
    credit = response["credit"]
    return credit


def get_date(response):
    date = response["date"]
    return date


def get_explanation(response):
    explanation = response["explanation"]
    return explanation


def get_hdurl(response):
    hdurl = response["hdurl"]
    return hdurl


def get_media_type(response):
    media_type = response["media_type"]
    return media_type


def get_permalink(response):
    permalink = response["permalink"]
    return permalink


def get_post_id(response):
    post_id = response["post_id"]
    return post_id


def get_title(response):
    title = response["title"]
    return title


def get_url(response):
    url = response["url"]
    return url


def download_image(url, date):
    if os.path.isfile(f"{date}.png") == False:
        raw_image = requests.get(url).content
        with open(f"{date}.jpg", "wb") as file:
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
