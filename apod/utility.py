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


def parse_apod(dt):
    if dt is None:
        dt = datetime.datetime.today()
    dt_str = dt.strftime("%y%m%d")
    apod_url = f"{API_BASE}/apod-basic/{dt_str}"
    res = requests.get(apod_url)
    j = res.json()
    return j


def parse_apod_range(date_from, date_to):
    apods = []

    # days_left = (date_to - date_from).days
    # d0 = date_from
    # d1 = date_to if days_left <= 25 else date_from + datetime.timedelta(days=25)

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

        # days_left = (date_to - d1).days
        # d0 = d1 + datetime.timedelta(days=1)
        # d1 = date_to if days_left <= 25 else d0 + datetime.timedelta(days=25)
    
    return apods


def apod_handler(
    apods, use_concept_tags=False, thumbs=False
):
    """
    Formats WP API responses to match legacy API format. Returns the response object to be
    served through the API.
    """
    if isinstance(apods, dict):
        apods = [apods]
    LOG.debug(f"_apod_handler called for {len(apods)} APODs")
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


# function for getting video thumbnails
def get_thumbs(data):
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


# # function for decoding response text into utf-8 or utf-16
# def _decode_response_text(res):
#     """
#     Decode APOD response bytes defensively because APOD occasionally serves
#     UTF-16 content while declaring UTF-8 in headers.
#     """
#     content = res.content or b""

#     if content.startswith(codecs.BOM_UTF16_LE) or content.startswith(codecs.BOM_UTF16_BE):
#         return content.decode("utf-16", errors="replace")

#     apparent = (res.apparent_encoding or "").lower()
#     if apparent.startswith("utf-16"):
#         return content.decode("utf-16", errors="replace")

#     if res.text:
#         return res.text

#     return content.decode("utf-8", errors="replace")


# # function that returns only last URL if there are multiple URLs stacked together
# def _get_last_url(data):
#     regex = re.compile("(?:.(?!http[s]?://))+$")
#     return regex.findall(data)[0]


# def _get_apod_chars(dt, thumbs):
#     media_type = "image"
#     if dt:
#         date_str = dt.strftime("%y%m%d")
#         apod_url = "%sap%s.html" % (BASE, date_str)
#     else:
#         apod_url = "%sastropix.html" % BASE
#     LOG.debug("OPENING URL:" + apod_url)
#     res = requests.get(apod_url)
#     page_text = _decode_response_text(res)
#     if res.status_code == 404:
#         return None
#         # LOG.error(f'No APOD entry for URL: {apod_url}')
#         # default_obj_path = 'static/default_apod_object.json'
#         # LOG.debug(f'Loading default APOD response from {default_obj_path}')
#         # with open(default_obj_path, 'r') as f:
#         #     default_obj_props = json.load(f)

#         # default_obj_props['date'] = dt.strftime('%Y-%m-%d')

#         # return default_obj_props

#     soup = BeautifulSoup(page_text, "html.parser")
#     LOG.debug("getting the data url")
#     hd_data = None
#     if soup.img:
#         # it is an image, so get both the low- and high-resolution data
#         data = BASE + str(soup.img["src"])
#         hd_data = data

#         LOG.debug("getting the link for hd_data")
#         for link in soup.find_all("a", href=True):
#             if link["href"] and str(link["href"]).startswith("image"):
#                 hd_data = BASE + str(link["href"])
#                 break
#     elif soup.iframe:
#         # its a video
#         media_type = "video"
#         data = soup.iframe["src"]
#     elif soup.video:
#         # its an HTML5 video <video> tag
#         media_type = "video"
#         data = ""
#         source_tag = soup.video.find("source")
#         if source_tag:
#             data = BASE + str(source_tag.get("src"))

#     else:
#         # it is neither image nor video, output empty urls
#         media_type = "other"
#         data = ""

#     props = {}

#     props["explanation"] = _explanation(soup)
#     props["title"] = _title(soup)
#     copyright_text = _copyright(soup)
#     if copyright_text:
#         props["copyright"] = copyright_text
#     props["media_type"] = media_type
#     if data:
#         props["url"] = _get_last_url(data)
#     if dt:
#         props["date"] = dt.strftime("%Y-%m-%d")
#     else:
#         props["date"] = _date(soup)

#     if hd_data:
#         props["hdurl"] = _get_last_url(hd_data)

#     if thumbs and media_type == "video":
#         if thumbs.lower() == "true":
#             props["thumbnail_url"] = _get_thumbs(data)

#     return props


# def _title(soup):
#     """
#     Accepts a BeautifulSoup object for the APOD HTML page and returns the
#     APOD image title.  Highly idiosyncratic with adaptations for different
#     HTML structures that appear over time.
#     """
#     LOG.debug("getting the title")
#     try:
#         # Handler for later APOD entries
#         number_of_center_elements = len(soup.find_all("center"))
#         if number_of_center_elements == 2:
#             center_selection = soup.find_all("center")[0]
#             bold_selection = center_selection.find_all("b")[0]
#             title = bold_selection.text.strip()
#             try:
#                 title = title.encode("latin1").decode("cp1252")
#             except (UnicodeEncodeError, UnicodeDecodeError):
#                 pass # text is already proper Unicode, leave it as-is
#             except Exception as ex:
#                 LOG.error(str(ex))
#         else:
#             center_selection = soup.find_all("center")[1]
#             bold_selection = center_selection.find_all("b")[0]
#             title = bold_selection.text.strip()
#             try:
#                 title = title.encode("latin1").decode("cp1252")
#             except (UnicodeEncodeError, UnicodeDecodeError):
#                 pass # text is already proper Unicode, leave it as-is
#             except Exception as ex:
#                 LOG.error(str(ex))

#         return title
#     except Exception:
#         # Handler for early APOD entries
#         text = soup.title.text.split(" - ")[-1]
#         title = text.strip()
#         try:
#             title = title.encode("latin1").decode("cp1252")
#         except (UnicodeEncodeError, UnicodeDecodeError):
#             pass # text is already proper Unicode, leave it as-is
#         except Exception as ex:
#             LOG.error(str(ex))

#         return title


# def _copyright(soup):
#     """
#     Accepts a BeautifulSoup object for the APOD HTML page and returns the
#     APOD image copyright.  Highly idiosyncratic with adaptations for different
#     HTML structures that appear over time.
#     """
#     LOG.debug("getting the copyright")
#     try:
#         # Handler for later APOD entries
#         # There's no uniform handling of copyright (sigh). Well, we just have to
#         # try every stinking text block we find...

#         copyright_text = None
#         use_next = False
#         for element in soup.find_all("a", string=True):
#             # LOG.debug("TEXT: "+element.text)

#             if use_next:
#                 copyright_text = element.text.strip()
#                 break

#             if "Copyright" in element.text:
#                 LOG.debug("Found Copyright text:" + str(element.text))
#                 use_next = True

#         if not copyright_text:
#             for element in soup.find_all(["b", "a"], string=True):
#                 # search text for explicit match
#                 if "Copyright" in element.text:
#                     LOG.debug("Found Copyright text:" + str(element.text))
#                     # pull the copyright from the link text which follows
#                     sibling = element.next_sibling
#                     stuff = ""
#                     while sibling:
#                         try:
#                             stuff = stuff + sibling.text
#                         except Exception:
#                             pass
#                         sibling = sibling.next_sibling

#                     if stuff:
#                         copyright_text = stuff.strip()

#         if copyright_text:
#             try:
#                 copyright_text = copyright_text.encode("latin1").decode("cp1252")
#             except (UnicodeEncodeError, UnicodeDecodeError):
#                 pass # text is already proper Unicode, leave it as-is
#             except Exception as ex:
#                 LOG.error(str(ex))

#         return copyright_text

#     except Exception as ex:
#         LOG.error(str(ex))
#         raise ValueError("Unsupported schema for given date.")


# def _explanation(soup):
#     """
#     Accepts a BeautifulSoup object for the APOD HTML page and returns the
#     APOD image explanation.  Highly idiosyncratic.
#     """
#     # Handler for later APOD entries
#     LOG.debug("getting the explanation")
#     s = soup.find_all("p")[2].text
#     s = s.replace("\n", " ")
#     s = s.replace("  ", " ")
#     s = s.strip(" ").strip("Explanation: ")
#     s = s.split(" Tomorrow's picture")[0]
#     s = s.strip(" ")
#     if s == "":
#         # Handler for earlier APOD entries
#         texts = [x.strip() for x in soup.text.split("\n")]
#         try:
#             begin_idx = texts.index("Explanation:") + 1
#         except ValueError as e:
#             # Rare case where "Explanation:" is not on its own line
#             explanation_line = [x for x in texts if "Explanation:" in x]
#             if len(explanation_line) == 1:
#                 begin_idx = texts.index(explanation_line[0])
#                 texts[begin_idx] = texts[begin_idx][12:].strip()
#             else:
#                 raise e

#         idx = texts[begin_idx:].index("")
#         s = " ".join(texts[begin_idx : begin_idx + idx])

#     try:
#         s = s.encode("latin1").decode("cp1252")
#     except (UnicodeEncodeError, UnicodeDecodeError):
#         pass # text is already proper Unicode, leave it as-is
#     except Exception as ex:
#         LOG.error(str(ex))

#     return s


# def _date(soup):
#     """
#     Accepts a BeautifulSoup object for the APOD HTML page and returns the
#     date of the APOD image.
#     """
#     LOG.debug("getting the date from soup data.")
#     _today = datetime.date.today()
#     for line in soup.text.split("\n"):
#         today_year = str(_today.year)
#         yesterday_year = str((_today - datetime.timedelta(days=1)).year)
#         # Looks for the first line that starts with the current year.
#         # This also checks yesterday's year so it doesn't break on January 1st at 00:00 UTC
#         # before apod.nasa.gov uploads a new image.
#         if line.startswith(today_year) or line.startswith(yesterday_year):
#             LOG.debug("found possible date match: " + line)
#             # takes apart the date string and turns it into a datetime
#             try:
#                 year, month, day = line.split()
#                 year = int(year)
#                 month = [
#                     "january",
#                     "february",
#                     "march",
#                     "april",
#                     "may",
#                     "june",
#                     "july",
#                     "august",
#                     "september",
#                     "october",
#                     "november",
#                     "december",
#                 ].index(month.lower()) + 1
#                 day = int(day)
#                 return datetime.date(year=year, month=month, day=day).strftime(
#                     "%Y-%m-%d"
#                 )
#             except:
#                 LOG.debug("unable to retrieve date from line: " + line)
#     raise Exception("Date not found in soup data.")


# def parse_apod_old(dt, use_default_today_date=False, thumbs=False):
#     """
#     Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
#     of that day, noting that
#     """

#     LOG.debug("apod chars called date:" + str(dt))

#     # try:
#     return _get_apod_chars(dt, thumbs)

#     # except Exception as ex:
#     #     # handle edge case where the service local time
#     #     # miss-matches with 'todays date' of the underlying APOD
#     #     # service (can happen because they are deployed in different
#     #     # timezones). Use the fallback of prior day's date

#     #     if use_default_today_date and dt:
#     #         # try to get the day before
#     #         dt = dt - datetime.timedelta(days=1)
#     #         return _get_apod_chars(dt, thumbs)
#     #     else:
#     #         # pass exception up the call stack
#     #         LOG.error(str(ex))
#     #         raise Exception(ex)

