''' A micro-service passing back enhanced information from Astronomy 
    Picture of the Day (APOD).
    
    Adapted from code in https://github.com/nasa/planetary-api
    Dec 1, 2015 (written by Dan Hammer) 

    @author=danhammer 
    @author=bathomas @email=brian.a.thomas@nasa.gov
'''

from datetime import datetime
from flask import request, jsonify, render_template, Flask
from flask_cors import CORS, cross_origin
from apod.utility import parse_apod, get_concepts 
import logging

app = Flask(__name__)
CORS(app)

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
#LOG.setLevel(logging.DEBUG)

# this should reflect both this service and the backing 
# assorted libraries
SERVICE_VERSION='v1'
APOD_METHOD_NAME='apod'
ALLOWED_APOD_FIELDS = ['concept_tags', 'date', 'hd']
ALCHEMY_API_KEY = None


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

def _usage(joinstr="', '", prestr="'"):
    return "Allowed request fields for "+APOD_METHOD_NAME+" method are "+prestr+joinstr.join(ALLOWED_APOD_FIELDS)

def _validate (data):
    LOG.debug("_validate(data) called")
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True

def _validate_date (dt):
    
    LOG.debug("_validate_date(dt) called")
    today = datetime.today()
    begin = datetime (1995, 6, 16)  # first APOD image date
    
    # validate input 
    if (dt > today) or (dt < begin):
        
        today_str = today.strftime('%b %d, %Y')
        begin_str = begin.strftime('%b %d, %Y')
        
        raise ValueError('Date must be between %s and %s.' % (begin_str, today_str))
        
def _apod_handler(dt, use_concept_tags=False, use_default_today_date=False):
    """Accepts a parameter dictionary. Returns the response object to be
    served through the API."""
    try:
        page_props = parse_apod(dt, use_default_today_date)
        LOG.debug("managed to get apod page characteristics")
        
        if use_concept_tags:
            if ALCHEMY_API_KEY == None:
                page_props['concepts'] = "concept_tags functionality turned off in current service"
            else:
                page_props['concepts'] = get_concepts(request, page_props['explanation'], ALCHEMY_API_KEY)
                
        return page_props 
    
    except Exception as e:
        
        LOG.error("Internal Service Error :"+str(type(e))+" msg:"+str(e))
        # return code 500 here
        return _abort(500, "Internal Service Error", usage=False)
    
#
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

    LOG.info("apod path called")
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

