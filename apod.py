
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime
import json

BASE = 'http://apod.nasa.gov/apod/'
http = urllib3.PoolManager()


def _concepts(text, apikey):
    """Returns the concepts associated with the text, interleaved with integer
    keys indicating the index."""
    cbase = 'http://access.alchemyapi.com/calls/text/TextGetRankedConcepts'

    params = dict(
        outputMode='json',
        apikey=apikey,
        text=text
    )

    response = json.loads(http.request('GET', cbase, fields=params).data)
    clist = [concept['text'] for concept in response['concepts']]
    return {k: v for k, v in zip(range(len(clist)), clist)}


def _title(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image title.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time."""
    try:
        # Handler for later APOD entries
        center_selection = soup.find_all('center')[1]
        bold_selection = center_selection.find_all('b')[0]
        return bold_selection.text.strip(' ')
    except Exception:
        # Handler for early APOD entries
        text = soup.title.text.split(' - ')[-1]
        return text.strip()
    else:
        raise ValueError('Unsupported schema for given date.')


def _explanation(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image explanation.  Highly idiosyncratic."""
    # Handler for later APOD entries
    s = soup.find_all('p')[2].text
    s = s.replace('\n', ' ')
    s = s.replace('  ', ' ')
    s = s.strip(' ').strip('Explanation: ')
    s = s.split(' Tomorrow\'s picture')[0]
    s = s.split('digg_url')[0]
    s = s.strip(' ')
    if s == '':
        # Handler for earlier APOD entries
        texts = [x.strip() for x in soup.text.split('\n')]
        begin_idx = texts.index('Explanation:') + 1
        idx = texts[begin_idx:].index('')
        s = (' ').join(texts[begin_idx:begin_idx + idx])
    return s


def apod_characteristics(date):
    """Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that """
    today = datetime.today()
    begin = datetime(1995, 06, 16)  # first APOD image date
    dt = datetime.strptime(date, '%Y-%m-%d')
    if (dt > today) or (dt < begin):
        today_str = today.strftime('%b %d, %Y')
        begin_str = begin.strftime('%b %d, %Y')
        raise ValueError(
            'Date must be between %s and %s.' % (begin_str, today_str)
        )
    else:
        try:
            date_str = dt.strftime('%y%m%d')
            url = '%sap%s.html' % (BASE, date_str)
            soup = BeautifulSoup(http.request('GET', url).data)
            suffix = soup.img['src']
            return _explanation(soup), _title(soup), BASE + suffix
        except Exception:
            raise ValueError('No APOD imagery for the given date.')


def apod_handler(params):
    """Accepts a parameter dictionary. Returns the response object to be
    served through the API."""
    try:
        d = {}
        explanation, title, url = apod_characteristics(params['date'])
        d['date'] = params['date']
        #d['concept_tags'] = bool(params['concept_tags'])
        d['url'] = url
        d['title'] = title
        d['explanation'] = explanation
        # if params['concept_tags'] == 'True':
        #    d['concepts'] = _concepts(explanation, params['apikey'])
        return d
    except Exception, e:
        m = 'Your request could not be processed.'
        m += ' Admins have been notified.'
        return dict(message=m, error=str(e))
