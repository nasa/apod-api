"""
Split off some library functions for easier testing and code management.

Created on Mar 24, 2017

@author=bathomas @email=brian.a.thomas@nasa.gov
"""

from bs4 import BeautifulSoup
import datetime
import requests
import logging
import json
import re
import urllib3

# import urllib.request

LOG = logging.getLogger(__name__)  # setting up logger
logging.basicConfig(level=logging.WARN)

# location of backing APOD service
BASE = 'https://apod.nasa.gov/apod/'

# Create urllib3 Pool Manager
http = urllib3.PoolManager()

# function for getting video thumbnails
def _get_thumbs(data):
    global video_thumb
    if "youtube" in data or "youtu.be" in data: # checking if video is from youtube
        # get ID from YouTube URL
        youtube_id_regex = re.compile("(?:(?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)")
        video_id = youtube_id_regex.findall(data)
        video_id = ''.join(''.join(elements) for elements in video_id).replace("?", "").replace("&", "")
        # get URL of thumbnail
        video_thumb = "https://img.youtube.com/vi/" + video_id + "/0.jpg"

    elif "vimeo" in data: # checking if video is from vimeo
        # get ID from Vimeo URL
        vimeo_id_regex = re.compile("(?:/video/)(\d+)")
        vimeo_id = vimeo_id_regex.findall(data)[0]
        # make an API call to get thumbnail URL
        vimeo_request = http.request("GET", "https://vimeo.com/api/v2/video/" + vimeo_id + ".json")
        data = json.loads(vimeo_request.data.decode('utf-8'))
        video_thumb = data[0]['thumbnail_large']
    else:
        # the thumbs parameter is True, but the APOD for the date is not a video, output nothing
        video_thumb = ""

    return video_thumb

# function that returns only last URL if there are multiple URLs stacked together
def _get_last_url(data):
    regex = re.compile("(?:.(?!http[s]?://))+$")
    return regex.findall(data)[0]

def _get_apod_chars(dt, thumbs):
    media_type = 'image'
    if dt:
        date_str = dt.strftime('%y%m%d') # converting date
        apod_url = '%sap%s.html' % (BASE, date_str) # adding to base
    else:
        apod_url = '%sastropix.html' % BASE # setting to default
    LOG.debug('OPENING URL:' + apod_url) # logging open url message
    res = requests.get(apod_url)
    
    if res.status_code == 404:
        return None
        # LOG.error(f'No APOD entry for URL: {apod_url}')
        # default_obj_path = 'static/default_apod_object.json'
        # LOG.debug(f'Loading default APOD response from {default_obj_path}')
        # with open(default_obj_path, 'r') as f:
        #     default_obj_props = json.load(f)

        # default_obj_props['date'] = dt.strftime('%Y-%m-%d')

        # return default_obj_props

    soup = BeautifulSoup(res.text, 'html.parser') # creating soup obj for html
    LOG.debug('getting the data url') # logs message
    hd_data = None
    if soup.img:
        # it is an image, so get both the low- and high-resolution data
        data = BASE + soup.img['src'] # adding base to src
        hd_data = data

        LOG.debug('getting the link for hd_data')
        for link in soup.find_all('a', href=True): # search for a tag
            if link['href'] and link['href'].startswith('image'):
                hd_data = BASE + link['href'] # adding base to found link
                break
    elif soup.iframe:
        # its a video
        media_type = 'video'
        data = soup.iframe['src']
    else:
        # it is neither image nor video, output empty urls
        media_type = 'other'
        data = ''

    props = {}

    props['explanation'] = _explanation(soup) # adding explanation to dict
    props['title'] = _title(soup) # adding title to dict
    copyright_text = _copyright(soup)
    if copyright_text:
        props['copyright'] = copyright_text # adding copyright to dict
    props['media_type'] = media_type # adding media type
    if data:
        props['url'] = _get_last_url(data) # adding url
    if dt:
        props['date'] = dt.strftime('%Y-%m-%d') # adding date
    else:
        props['date'] = _date(soup)

    if hd_data:
        props['hdurl'] = _get_last_url(hd_data) # adding hd data

    if thumbs and media_type == "video":
        if thumbs.lower() == "true":
            props['thumbnail_url'] = _get_thumbs(data) # adding video


    return props             ## Return dictionary


def _title(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image title.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time.
    """
    LOG.debug('getting the title')
    try:
        # Handler for later APOD entries
        number_of_center_elements = len(soup.find_all('center')) # finds all center tags in HTML doc
        if(number_of_center_elements == 2): # checks number of elements
            center_selection = soup.find_all('center')[0] # gets center tags
            bold_selection = center_selection.find_all('b')[0] # finds all b tags in HTML doc 
            title = bold_selection.text.strip(' ') # removes whitespace
            try:
                title = title.encode('latin1').decode('cp1252') # encodes text in latin1 format --> decodese in cp1252 format
            except Exception as ex:
                LOG.error(str(ex)) # if exception raise error
        else: # other cases
            center_selection = soup.find_all('center')[1] # gets center tags
            bold_selection = center_selection.find_all('b')[0] # gets b tags
            title = bold_selection.text.strip(' ') # removes whitespace
            try:
                title = title.encode('latin1').decode('cp1252') # encodes in latin1 --> decodes in cp1252
            except Exception as ex:
                LOG.error(str(ex)) # if exception raise error
        
        return title
    except Exception:
        # Handler for early APOD entries
        text = soup.title.text.split(' - ')[-1] # gets title tag from HTML doc
        title = text.strip() # removes whitespace
        try:
            title = title.encode('latin1').decode('cp1252') # encodes in latin1 --> decoes in cp1252
        except Exception as ex:
            LOG.error(str(ex)) # if exception raise error

        return title


def _copyright(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image copyright.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time.
    """
    LOG.debug('getting the copyright')
    try:
        # Handler for later APOD entries
        # There's no uniform handling of copyright (sigh). Well, we just have to
        # try every stinking text block we find...

        copyright_text = None
        use_next = False
        for element in soup.findAll('a', text=True): # searching for a tags
            # LOG.debug("TEXT: "+element.text)

            if use_next:
                copyright_text = element.text.strip(' ') # stripping copyright
                break

            if 'Copyright' in element.text:
                LOG.debug('Found Copyright text:' + str(element.text)) # appending given copyright
                use_next = True

        if not copyright_text:

            for element in soup.findAll(['b', 'a'], text=True): # searching for b and a tags
                # search text for explicit match
                if 'Copyright' in element.text:
                    LOG.debug('Found Copyright text:' + str(element.text)) # appending copyright
                    # pull the copyright from the link text which follows
                    sibling = element.next_sibling
                    stuff = ""
                    while sibling:
                        try:
                            stuff = stuff + sibling.text # getting cr from next text
                        except Exception:
                            pass
                        sibling = sibling.next_sibling

                    if stuff:
                        copyright_text = stuff.strip(' ') # stripping text
        try:
            copyright_text = copyright_text.encode('latin1').decode('cp1252') # encoding copyright in latin1 and decoding in cp1252
        except Exception as ex:
            LOG.error(str(ex)) # logging error

        return copyright_text

    except Exception as ex:
        LOG.error(str(ex))
        raise ValueError('Unsupported schema for given date.') # raises exception


def _explanation(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image explanation.  Highly idiosyncratic.
    """
    # Handler for later APOD entries
    LOG.debug('getting the explanation')
    s = soup.find_all('p')[2].text # searching for p tags
    s = s.replace('\n', ' ')
    s = s.replace('  ', ' ')
    s = s.strip(' ').strip('Explanation: ') #stripping titles
    s = s.split(' Tomorrow\'s picture')[0]
    s = s.strip(' ')
    if s == '':
        # Handler for earlier APOD entries
        texts = [x.strip() for x in soup.text.split('\n')]
        try:
            begin_idx = texts.index('Explanation:') + 1 # grabbing explanation
        except ValueError as e:
            # Rare case where "Explanation:" is not on its own line
            explanation_line = [x for x in texts if "Explanation:" in x]
            if len(explanation_line) == 1:
                begin_idx = texts.index(explanation_line[0]) # grabbing explanation
                texts[begin_idx] = texts[begin_idx][12:].strip()
            else:
                raise e

        idx = texts[begin_idx:].index('')
        s = ' '.join(texts[begin_idx:begin_idx + idx]) # joining explanation text

    try:
        s = s.encode('latin1').decode('cp1252') # encoding latin1 decoding cp1252
    except Exception as ex:
        LOG.error(str(ex)) # raising exception

    return s


def _date(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    date of the APOD image.
    """
    LOG.debug('getting the date from soup data.') # logging  message getting date
    _today = datetime.date.today() # todays date
    for line in soup.text.split('\n'):
        today_year = str(_today.year) # getting year
        yesterday_year = str((_today-datetime.timedelta(days=1)).year) # getting yesterdays year 
        # Looks for the first line that starts with the current year.
        # This also checks yesterday's year so it doesn't break on January 1st at 00:00 UTC
        # before apod.nasa.gov uploads a new image.
        if line.startswith(today_year) or line.startswith(yesterday_year):
            LOG.debug('found possible date match: ' + line)
            # takes apart the date string and turns it into a datetime
            try:
                year, month, day = line.split()
                year = int(year)
                month = ['january', 'february', 'march', 'april',
                         'may', 'june', 'july', 'august',
                         'september', 'october', 'november', 'december'
                         ].index(month.lower()) + 1
                day = int(day)
                return datetime.date(year=year, month=month, day=day).strftime('%Y-%m-%d') # return date converted to datetime
            except:
                LOG.debug('unable to retrieve date from line: ' + line) # logging error message
    raise Exception('Date not found in soup data.') # raising exception


def parse_apod(dt, use_default_today_date=False, thumbs=False):
    """
    Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that
    """

    LOG.debug('apod chars called date:' + str(dt)) # logging message apod chars

    try:
        return _get_apod_chars(dt, thumbs) # try return apod chars func

    except Exception as ex:

        # handle edge case where the service local time
        # miss-matches with 'todays date' of the underlying APOD
        # service (can happen because they are deployed in different
        # timezones). Use the fallback of prior day's date

        if use_default_today_date and dt:
            # try to get the day before
            dt = dt - datetime.timedelta(days=1)
            return _get_apod_chars(dt, thumbs)
        else:
            # pass exception up the call stack
            LOG.error(str(ex))
            raise Exception(ex)


def get_concepts(request, text, apikey):
    """
    Returns the concepts associated with the text, interleaved with integer
    keys indicating the index.
    """
    cbase = 'http://access.alchemyapi.com/calls/text/TextGetRankedConcepts'

    params = dict( # concept params
        outputMode='json',
        apikey=apikey,
        text=text
    )

    try:

        LOG.debug('Getting response') # logging message getting response
        response = json.loads(request.get(cbase, fields=params)) # converting response into json
        clist = [concept['text'] for concept in response['concepts']] # concept list
        return {k: v for k, v in zip(range(len(clist)), clist)}

    except Exception as ex:
        raise ValueError(ex) # raising exception
