''' A micro-service passing back enhanced information from Astronomy 
    Picture of the Day (APOD).
    
    Adapted from code in https://github.com/nasa/planetary-api
    Dec 1, 2015 (written by Dan Hammer) 

    @author=danhammer 
    @author=bathomas @email=brian.a.thomas@nasa.gov
'''

from bs4 import BeautifulSoup
from datetime import datetime
from flask import request, jsonify, render_template, Flask
from flask.ext.cors import CORS
import json
import requests
import logging

app = Flask(__name__)
CORS(app)

LOG = logging.getLogger(__name__)

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
    print ("WARNING: NO alchemy_api.key found, concept_tagging is NOT supported")

def _abort(code, msg, usage=True):

    if (usage):
        msg += " "+_usage()+"'" 

    response = jsonify(service_version=SERVICE_VERSION, msg=msg)
    response.status_code = code
    print (str(response))
    return response

def _apod_characteristics(date):
    """Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that """
    today = datetime.today()
    begin = datetime (1995, 6, 16)  # first APOD image date
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
            soup = BeautifulSoup(requests.get(url).text, "html.parser")
            suffix = soup.img['src']
            hd_suffix = suffix
            
            for link in soup.find_all('a', href=True):
                print ("link:"+str(link))
                if link['href'] and link['href'].startswith("image"):
                    print ("  href:"+str(link['href']))
                    hd_suffix = link['href']
                    break
            
            return _explanation(soup), _title(soup), _copyright(soup), BASE + suffix, BASE + hd_suffix
        
        except Exception as ex:
            print ("EXCEPTION: "+str(ex))
            # this most probably should return code 500 here
            raise ValueError('No APOD imagery for the given date.')

def _apod_handler(date, use_concept_tags=False):
    """Accepts a parameter dictionary. Returns the response object to be
    served through the API."""
    try:
        d = {}
        d['date'] = date
        explanation, title, copyright, url, hdurl = _apod_characteristics(date)
        d['explanation'] = explanation
        d['title'] = title
        d['url'] = url
        d['hdurl'] = hdurl
        if copyright:
            d['copyright'] = copyright
        if use_concept_tags:
            if ALCHEMY_API_KEY == None:
                d['concepts'] = "concept_tags functionality turned off in current service"
            else:
                d['concepts'] = _concepts(explanation, ALCHEMY_API_KEY)
        return d
    except Exception as e:
        m = 'Your request could not be processed.'
        return dict(message=m, error=str(e))
    
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
        
        print ("Getting response")
        response = json.loads(request.get(cbase, fields=params))
        clist = [concept['text'] for concept in response['concepts']]
        return {k: v for k, v in zip(range(len(clist)), clist)}
    
    except Exception as ex:
        print (str(ex))
        raise ValueError(ex)


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

def _copyright(soup):
    """Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image copyright.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time."""
    try:
        # Handler for later APOD entries
        center_selection = soup.find_all('center')[1]
        bold_selection = center_selection.find_all('b')[1]
        if "Copyright" in bold_selection.text:
            # pull the copyright from the link text
            link_selection = center_selection.find_all('a')[0]
            if "Copyright" in link_selection.text:
                # hmm. older style, try to grab from 2nd link
                link_selection = center_selection.find_all('a')[1]
            return link_selection.text.strip(' ')
        else:
            # NO stated copyright, so we return None
            return None
    except Exception:
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

def _usage(joinstr="', '", prestr="'"):
    return "Allowed request fields for "+APOD_METHOD_NAME+" method are "+prestr+joinstr.join(ALLOWED_APOD_FIELDS)

def _validate (data):
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True

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
        
        date = args.get('date', datetime.strftime(datetime.today(), '%Y-%m-%d'))
        use_concept_tags = args.get('concept_tags', False)
        
        # get data
        data = _apod_handler(date, use_concept_tags)
        data['service_version'] = SERVICE_VERSION
        
        # return info as JSON
        return jsonify(data)

    except Exception as ex:

        etype = type(ex)
        #print (str(etype)+"\n "+str(ex))
        if etype == ValueError or "BadRequest" in str(etype):
            return _abort(400, str(ex)+".")
        else:
            print ("Service Exception. Msg: "+str(type(ex))) 
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

