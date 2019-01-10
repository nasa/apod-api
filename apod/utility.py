"""
Split off some library functions for easier testing and code management.

Created on Mar 24, 2017

@author=bathomas @email=brian.a.thomas@nasa.gov
"""

from bs4 import BeautifulSoup
from datetime import timedelta
import requests
import logging
import json

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

# location of backing APOD service
BASE = 'https://apod.nasa.gov/apod/'


def _get_apod_chars(dt):
    media_type = 'image'
    date_str = dt.strftime('%y%m%d')
    apod_url = '%sap%s.html' % (BASE, date_str)
    LOG.debug('OPENING URL:' + apod_url)
    soup = BeautifulSoup(requests.get(apod_url).text, 'html.parser')
    LOG.debug('getting the data url')
    hd_data = None
    if soup.img:
        # it is an image, so get both the low- and high-resolution data
        data = BASE + soup.img['src']
        hd_data = data

        LOG.debug('getting the link for hd_data')
        for link in soup.find_all('a', href=True):
            if link['href'] and link['href'].startswith('image'):
                hd_data = BASE + link['href']
                break
    else:
        # its a video
        media_type = 'video'
        data = soup.iframe['src']

    props = {}

    props['explanation'] = _explanation(soup)
    props['title'] = _title(soup)
    copyright_text = _copyright(soup)
    if copyright_text:
        props['copyright'] = copyright_text
    props['media_type'] = media_type
    props['url'] = data
    props['date'] = dt.isoformat()

    if hd_data:
        props['hdurl'] = hd_data

    return props


def _title(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image title.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time.
    """
    LOG.debug('getting the title')
    try:
        # Handler for later APOD entries
        center_selection = soup.find_all('center')[1]
        bold_selection = center_selection.find_all('b')[0]
        return bold_selection.text.strip(' ')
    except Exception:
        # Handler for early APOD entries
        text = soup.title.text.split(' - ')[-1]
        return text.strip()


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
        for element in soup.findAll('a', text=True):
            # LOG.debug("TEXT: "+element.text)

            if use_next:
                copyright_text = element.text.strip(' ')
                break

            if 'Copyright' in element.text:
                LOG.debug('Found Copyright text:' + str(element.text))
                use_next = True

        if not copyright_text:

            for element in soup.findAll(['b', 'a'], text=True):
                # search text for explicit match
                if 'Copyright' in element.text:
                    LOG.debug('Found Copyright text:' + str(element.text))
                    # pull the copyright from the link text which follows
                    sibling = element.next_sibling
                    stuff = ""
                    while sibling:
                        try:
                            stuff = stuff + sibling.text
                        except Exception:
                            pass
                        sibling = sibling.next_sibling

                    if stuff:
                        copyright_text = stuff.strip(' ')

        return copyright_text

    except Exception as ex:
        LOG.error(str(ex))
        raise ValueError('Unsupported schema for given date.')


def _explanation(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image explanation.  Highly idiosyncratic.
    """
    # Handler for later APOD entries
    LOG.debug('getting the explanation')
    s = soup.find_all('p')[2].text
    s = s.replace('\n', ' ')
    s = s.replace('  ', ' ')
    s = s.strip(' ').strip('Explanation: ')
    s = s.split(' Tomorrow\'s picture')[0]
    s = s.strip(' ')
    if s == '':
        # Handler for earlier APOD entries
        texts = [x.strip() for x in soup.text.split('\n')]
        try:
            begin_idx = texts.index('Explanation:') + 1
        except ValueError as e:
            # Rare case where "Explanation:" is not on its own line
            explanation_line = [x for x in texts if "Explanation:" in x]
            if len(explanation_line) == 1:
                begin_idx = texts.index(explanation_line[0])
                texts[begin_idx] = texts[begin_idx][12:].strip()
            else:
                raise e

        idx = texts[begin_idx:].index('')
        s = ' '.join(texts[begin_idx:begin_idx + idx])
    return s


def parse_apod(dt, use_default_today_date=False):
    """
    Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that
    """

    LOG.debug('apod chars called date:' + str(dt))

    try:
        return _get_apod_chars(dt)

    except Exception as ex:

        # handle edge case where the service local time
        # miss-matches with 'todays date' of the underlying APOD
        # service (can happen because they are deployed in different
        # timezones). Use the fallback of prior day's date 

        if use_default_today_date:
            # try to get the day before
            dt = dt - timedelta(days=1)
            return _get_apod_chars(dt)
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

    params = dict(
        outputMode='json',
        apikey=apikey,
        text=text
    )

    try:

        LOG.debug('Getting response')
        response = json.loads(request.get(cbase, fields=params))
        clist = [concept['text'] for concept in response['concepts']]
        return {k: v for k, v in zip(range(len(clist)), clist)}

    except Exception as ex:
        raise ValueError(ex)
