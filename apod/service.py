''' A micro-service passing back enhanced information from Astronomy 
    Picture of the Day (APOD).
    
    Adapted from code in https://github.com/nasa/planetary-api
    Dec 1, 2015 (written by Dan Hammer) 

    @author=danhammer 
    @author=bathomas @email=brian.a.thomas@nasa.gov
'''

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import request, jsonify, render_template, Flask
from flask.ext.cors import CORS
import json
import requests
import logging

app = Flask(__name__)
CORS(app)

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)
#LOG.setLevel(logging.DEBUG)

# this should reflect both this service and the backing 
# assorted libraries
SERVICE_VERSION='v1'
APOD_METHOD_NAME='apod'
ALLOWED_APOD_FIELDS = ['concept_tags', 'date', 'hd']
ALCHEMY_API_KEY = None

# location of backing APOD service
BASE = 'http://apod.nasa.gov/apod/'

try:
    with open('alchemy_api.key', 'r') as f:
        ALCHEMY_API_KEY = f.read()
except:
    LOG.info ("WARNING: NO alchemy_api.key found, concept_tagging is NOT supported")

def _abort(code, msg, usage=True):

    if (usage):
        msg += " "+_usage()+"'" 

    response = jsonify(service_version=SERVICE_VERSION, msg=msg, code=code)
    response.status_code = code
    LOG.debug(str(response))
    
    return response

def _get_apod_chars(dt):
    
    media_type = 'image'
    date_str = dt.strftime('%y%m%d')
    apod_url = '%sap%s.html' % (BASE, date_str)
    LOG.debug("OPENING URL:"+apod_url)
    soup = BeautifulSoup(requests.get(apod_url).text, "html.parser")
    LOG.debug("getting the data url")
    data = None
    hd_data = None
    if soup.img:
        # it is an image, so get both the low- and high-resolution data
        data = BASE + soup.img['src']
        hd_data = data
        
        LOG.debug("getting the link for hd_data")
        for link in soup.find_all('a', href=True):
            if link['href'] and link['href'].startswith("image"):
                hd_data = BASE + link['href']
                break
    else:
        # its a video
        media_type = 'video'
        data = soup.iframe['src']
    
    return _explanation(soup), _title(soup), _copyright(soup), data, hd_data, media_type
        
        
def _apod_characteristics(dt, use_default_today_date=False):
    """Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that """

    LOG.debug("apod chars called")
    
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
            raise Exception(ex)
                
def _apod_handler(dt, use_concept_tags=False, use_default_today_date=False):
    """Accepts a parameter dictionary. Returns the response object to be
    served through the API."""
    try:
        d = {}
        explanation, title, copyright, url, hdurl, media_type = _apod_characteristics(dt, use_default_today_date)
        LOG.debug("managed to get apod characteristics")
        d['explanation'] = explanation
        d['title'] = title
        d['url'] = url
        if hdurl:
            d['hdurl'] = hdurl
        d['media_type'] = media_type
        if copyright:
            d['copyright'] = copyright
        if use_concept_tags:
            if ALCHEMY_API_KEY == None:
                d['concepts'] = "concept_tags functionality turned off in current service"
            else:
                d['concepts'] = _concepts(explanation, ALCHEMY_API_KEY)
        return d
    
    except Exception as e:
        
        LOG.error("Internal Service Error :"+str(type(e))+" msg:"+str(e))
        # return code 500 here
        return _abort(500, "Internal Service Error", usage=False)
    
def _concepts(text, apikey):
    """Returns the concepts associated with the text, interleaved with integer
    keys indicating the index."""
    cbase = 'http://access.alchemyapi.com/calls/text/TextGetRankedConcepts'
    
    params = dict(
        outputMode='json',
        apikey=apikey,
        text=text
    )

    try:
        
        LOG.debug("Getting response")
        response = json.loads(request.get(cbase, fields=params))
        clist = [concept['text'] for concept in response['concepts']]
        return {k: v for k, v in zip(range(len(clist)), clist)}
    
    except Exception as ex:
        raise ValueError(ex)


def _title(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image title.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time."""
    LOG.debug("getting the title")
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

def _copyright(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image copyright.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time."""
    LOG.debug("getting the copyright")
    try:
        # Handler for later APOD entries

        # There's no uniform handling of copyright (sigh). Well, we just have to 
        # try every stinking text block we find...

        for element in soup.findAll('b', text=True):
            #LOG.debug("TEXT: "+element.text)
            # search text for explicit match
            if "Copyright" in element.text:
                LOG.debug("Found Copyright text:"+str(element.text))
                LOG.debug("                element:"+str(element))
                # pull the copyright from the link text
                link_selection = element.parent.find_all('a')[0] 
                if "Copyright" in link_selection.text:
                    # hmm. older style, try to grab from 2nd link
                    LOG.debug("trying olderstyle copyright grab")
                    link_selection = element.parent.find_all('a')[1]
                # return
                return link_selection.text.strip(' ')

    except Exception as ex:
        LOG.error(str(ex))
        raise ValueError('Unsupported schema for given date.')

    # NO stated copyright, so we return None
    return None

def _explanation(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image explanation.  Highly idiosyncratic."""
    # Handler for later APOD entries
    LOG.debug("getting the explanation")
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

def _usage(joinstr="', '", prestr="'"):
    return "Allowed request fields for "+APOD_METHOD_NAME+" method are "+prestr+joinstr.join(ALLOWED_APOD_FIELDS)

def _validate (data):
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True

def _validate_date (dt):
    
    today = datetime.today()
    begin = datetime (1995, 6, 16)  # first APOD image date
    
    # validate input 
    if (dt > today) or (dt < begin):
        
        today_str = today.strftime('%b %d, %Y')
        begin_str = begin.strftime('%b %d, %Y')
        
        raise ValueError('Date must be between %s and %s.' % (begin_str, today_str))
        
    
# Endpoints
#

@app.route('/')
def home():
    return render_template('home.html', version=SERVICE_VERSION, \
                            service_url=request.host, \
                            methodname=APOD_METHOD_NAME, \
			    usage=_usage(joinstr='", "', prestr='"')+'"')

@app.route('/'+SERVICE_VERSION+'/'+APOD_METHOD_NAME+'/', methods=['GET'])
def apod():

    try:

        # application/json GET method 
        args = request.args

        if not _validate(args):
            return _abort (400, "Bad Request incorrect field passed.")
        
        # get the date param
        use_default_today_date = False
        date = args.get('date')
        if not date:
            # fall back to using today's date IF they didn't specify a date
            date = datetime.strftime(datetime.today(), '%Y-%m-%d')
            use_default_today_date = True
            
        # grab the concept_tags param
        use_concept_tags = args.get('concept_tags', False)
        
        # validate input date
        dt = datetime.strptime(date, '%Y-%m-%d')
        _validate_date(dt)
        
        # get data
        data = _apod_handler(dt, use_concept_tags, use_default_today_date)
        data['date'] = date
        data['service_version'] = SERVICE_VERSION
        
        # return info as JSON
        return jsonify(data)

    except ValueError as ve:
        return _abort(400, str(ve), False)
        
    except Exception as ex:

        etype = type(ex)
        if etype == ValueError or "BadRequest" in str(etype):
            return _abort(400, str(ex)+".")
        else:
            LOG.error("Service Exception. Msg: "+str(type(ex))) 
            return _abort(500, "Internal Service Error", usage=False)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return _abort(404, "Sorry, Nothing at this URL.", usage=True)


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return _abort('Sorry, unexpected error: {}'.format(e), usage=False)


if __name__ == '__main__':
    app.run()

