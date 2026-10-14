"""
Split off some library functions for easier testing and code management.

Created on Mar 24, 2017

@author=bathomas @email=brian.a.thomas@nasa.gov
"""

import codecs
import datetime
import json
import logging
import re

import requests
import urllib3
from bs4 import BeautifulSoup

# import urllib.request

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.WARN)

# location of backing APOD service
# BASE = "https://apod.nasa.gov/apod/"
BASE = "https://science.nasa.gov/"
API_BASE = "https://science.nasa.gov/wp-json/wp/v2"

# Create urllib3 Pool Manager
http = urllib3.PoolManager()


def parse_apod(date, fallback=False):
    """
    Get an APOD from the Wordpress JSON API.

    :param: date: datetime.date object, the date to request.
    :param: fallback: bool indicating whether to fall back to the previous date if a request 404s,
    should be used if using a default date in case the latest APOD hasn't been posted yet.
    :return: dict containing APOD data.
    """
    date_str = date.strftime("%y%m%d")
    apod_url = f"{API_BASE}/apod-basic/{date_str}"
    res = requests.get(apod_url)
    if res.status_code == 404 and fallback:
        LOG.debug("404 on current date, falling back on to previous date")
        new_date = date - datetime.timedelta(days=1)
        return parse_apod(new_date, False) # only fall back one day
    j = res.json()
    return j


def parse_apod_range(date_from, date_to):
    """
    Get a range of APOD dates from the Wordpress JSON API. Ranges are end-inclusive.

    :param: date_from: datetime.date object, the starting date of the range to request.
    :param: date_to: datetime.date object, the end date of the range to request.
    :return: list of dicts containing APOD data.
    """
    apods = []

    page = 1
    j = None

    while j is None or len(j) > 0:

        date_from_str = date_from.strftime("%y%m%d")
        date_to_str = date_to.strftime("%y%m%d")

        apod_url = f"{API_BASE}/apod-basic?date_from={date_from_str}&date_to={date_to_str}&page={page}"
        res = requests.get(apod_url)
        j = res.json()
        apods.extend(j)

        page += 1
    
    # should be ordered earliest date to latest date
    apods.reverse()
    return apods


def apod_handler(
    apods: list | dict, use_concept_tags=False, thumbs=False
):
    """
    Formats WP API responses to match legacy API format. Returns the response object to be
    served through the API.

    :param: apods: list of dicts containing APOD data, if processing a range.
    Single dict, if processing one APOD.
    :param: use_concept_tags: bool indicating whether to get concept tags, if available. 
    :param: thumbs: bool indicating whether to get thumbnails, if media_type is "video".
    """
    if isinstance(apods, dict):
        apods = [apods]
    LOG.debug(f"apod_handler called for {len(apods)} APODs")
    out_apods = []
    try:
        for apod in apods:
            out_apod = {}

            # WP API returns explanation in HTML format, fix for backwards compatibility
            # (note that soup is already a dependency. this part is all it's being used for now)
            if "explanation" in apod:
                out_apod["explanation"] = extract_text(apod["explanation"])

            if "title" in apod:
                out_apod["title"] = apod["title"]

            if "copyright" in apod:
                out_apod["copyright"] = extract_text(apod["copyright"])

            if "media_type" in apod:
                out_apod["media_type"] = apod["media_type"]

            # WP API returns page URL rather than image/video URL in "url" field,
            # fix for backwards compatibility
            if "hdurl" in apod:
                out_apod["url"] = apod["hdurl"]
                out_apod["hdurl"] = apod["hdurl"]

            # add permalink since the page URL can no longer be guessed,
            # even though it wasn't part of the original API
            if "permalink" in apod:
                out_apod["permalink"] = apod["permalink"]

            if "date" in apod:
                out_apod["date"] = apod["date"]

            if "service_version" in apod:
                out_apod["service_version"] = apod["service_version"]

            # concept tags
            if use_concept_tags:
                if ALCHEMY_API_KEY is None:
                    out_apod["concepts"] = (
                        "concept_tags functionality turned off in current service"
                    )
                else:
                    out_apod["concepts"] = get_concepts(
                        request, out_apod["explanation"], ALCHEMY_API_KEY
                    )

            # thumbs
            if thumbs and media_type == "video":
                if thumbs.lower() == "true":
                    page_props["thumbnail_url"] = get_thumbs(page_props["hdurl"])
            
            out_apods.append(out_apod)

        if len(out_apods) == 1:
            return out_apods[0]
        else:
            return out_apods

    except Exception as e:
        LOG.error("Internal Service Error :" + str(type(e)) + " msg:" + str(e))
        # return code 500 here
        return _abort(500, "Internal Service Error", usage=False)


def get_thumbs(data):
    """
    Get a video thumbnail URL, given a YouTube or Vimeo URL.
    """
    global video_thumb
    if "youtube" in data or "youtu.be" in data:
        # get ID from YouTube URL
        youtube_id_regex = re.compile(
            r"(?:(?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)"
        )
        video_id = youtube_id_regex.findall(data)
        video_id = (
            "".join("".join(elements) for elements in video_id)
            .replace("?", "")
            .replace("&", "")
        )
        # get URL of thumbnail
        video_thumb = "https://img.youtube.com/vi/" + video_id + "/0.jpg"
    elif "vimeo" in data:
        # get ID from Vimeo URL
        vimeo_id_regex = re.compile(r"(?:/video/)(\d+)")
        vimeo_id = vimeo_id_regex.findall(data)[0]
        # make an API call to get thumbnail URL
        vimeo_request = http.request(
            "GET", "https://vimeo.com/api/v2/video/" + vimeo_id + ".json"
        )
        data = json.loads(vimeo_request.data.decode("utf-8"))
        video_thumb = data[0]["thumbnail_large"]
    else:
        # the thumbs parameter is True, but the APOD for the date is not a video, output nothing
        video_thumb = ""

    return video_thumb


def get_concepts(request, text, apikey):
    """
    Returns the concepts associated with the text, interleaved with integer
    keys indicating the index.
    """
    cbase = "http://access.alchemyapi.com/calls/text/TextGetRankedConcepts"

    params = dict(outputMode="json", apikey=apikey, text=text)

    try:
        LOG.debug("Getting response")
        response = json.loads(request.get(cbase, fields=params))
        clist = [concept["text"] for concept in response["concepts"]]
        return {k: v for k, v in zip(range(len(clist)), clist)}

    except Exception as ex:
        raise ValueError(ex)


def extract_text(explanation):
    """
    Removes the actual text from an HTML string.
    Provides backwards compatibility with previous scraper API.
    """
    soup = BeautifulSoup(explanation, "html.parser")
    return (
        soup.get_text()
        .removeprefix("Explanation:")
        .strip()
    )
