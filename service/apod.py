''' A micro-service passing back enhanced information from Astronomy 
    Picture of the Day (APOD).
    
    Adapted from code in http://github.com/nasa/planetary-api
    Dec 1, 2015 

    @author=bathomas @email=brian.a.thomas@nasa.gov
'''

from flask import request, jsonify, render_template, Response, Flask
import json

app = Flask(__name__)

# this should reflect both this service and the backing 
# assorted libraries
SERVICE_VERSION='v1'

# Load default config and override config from an environment variable
app.config.update(dict(
    # the name of the file which contains the model (dictionary)
    # of terms we will use for tagging
    DICTIONARY_NAME = os.path.join("data","nasa_opendata_dictionary.pkl"),
  )
)  

# The object instance which will do the work

def init():
   import pickle
   dict_file = os.path.realpath(app.config['DICTIONARY_NAME'])
   print ("initializing using :"+dict_file)
   with open (dict_file, 'rb+') as f:
       dictionary = pickle.load(f)
       app.config['TERM_EXTRACTOR'] = t.UnstructuredTextTermExtractor(dictionary)

def _abort(code, msg, usage=True):

    if (usage):
        msg += " "+_usage()+"'" 

    response = jsonify(service_version=SERVICE_VERSION, msg=msg)
    response.status_code = code
    return response

def _usage(joinstr="', '", prestr="'"):
    return "Allowed request fields for "+apod_METHOD_NAME+" method are "+prestr+joinstr.join(ALLOWED_apod_FIELDS)

def _validate(data):

    for key in data:
       if key not in ALLOWED_apod_FIELDS:
           return False
    return True

# Endpoints
#

@app.route('/')
def home():
    return render_template('home.html', version=SERVICE_VERSION, \
                            service_url=request.host, \
                            methodname=apod_METHOD_NAME, \
			    usage=_usage(joinstr='", "', prestr='"')+'"')



@app.route('/'+SERVICE_VERSION+'/apod/', methods=['GET','OPTIONS'])
def apod():

    try:
        if not app.config['TERM_EXTRACTOR']:  
            init()

        # trap OPTIONS method to handle the x-site issue
        if request.method == "OPTIONS": 
            response = Response("", status=200, mimetype='application/json') 
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Max-Age'] = 1000
            # note that '*' is not valid for Access-Control-Allow-Headers
            response.headers['Access-Control-Allow-Headers'] = 'origin, x-csrftoken, content-type, accept'
            return response

        # application/json POST method 
        data = request.get_json(force=True)

        if not _validate(data):
            return _abort (400, "Bad Request incorrect field passed.")

        text=''
        if 'text' not in data:
            return _abort (400, "NO passed text field ..._abort.")
        else:
            text = data.get('text')

        highest_colocation = app.config['DEFAULT_HIGHEST_NGRAM']
        if 'highest_ngram_allowed' in data:
            highest_colocation = int(data.get('highest_ngram_allowed'))
    
        term_count_threshold = app.config['DEFAULT_TERM_COUNT_THRESHOLD']
        if 'term_count_threshold' in data:
            term_count_threshold = int(data.get('term_count_threshold'))

        # run the text term extractor here
        keywords=app.config['TERM_EXTRACTOR'].apod([text], highest_colocation=highest_colocation, min_term_count=term_count_threshold)

        # return info as JSON
        return jsonify(service_version=SERVICE_VERSION,\
                       textmining_library_version=app.config['LIBRARY_VERSION'],\
                       dictionary=app.config['DICTIONARY_NAME'],\
                       highest_ngram_allowed=highest_colocation,\
                       term_count_threshold=term_count_threshold,\
                       keywords=keywords)

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

