"""
A micro-service passing back enhanced information from Astronomy
Picture of the Day (APOD).

Adapted from code in https://github.com/nasa/planetary-api
Dec 1, 2015 (written by Dan Hammer)

@author=danhammer
@author=bathomas @email=brian.a.thomas@nasa.gov
@author=jnbetancourt @email=jennifer.n.betancourt@nasa.gov

adapted for AWS Elastic Beanstalk deployment
@author=JustinGOSSES @email=justin.c.gosses@nasa.gov
"""
import sys
sys.path.insert(0, "../lib")
### justin edit
sys.path.insert(1, ".")

from datetime import datetime, date
from random import shuffle
from flask import request, jsonify, render_template, Flask, current_app
from flask_cors import CORS
from apod.utility import parse_apod, get_concepts
import logging

#### added by justin for EB
#from wsgiref.simple_server import make_server

application = Flask(__name__)
CORS(application, resources={r"/*": {"expose_headers": ["X-RateLimit-Limit","X-RateLimit-Remaining"]} })

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# this should reflect both this service and the backing
# assorted libraries
SERVICE_VERSION = 'v1'
APOD_METHOD_NAME = 'apod'
ALLOWED_APOD_FIELDS = ['concept_tags', 'date', 'hd', 'count', 'start_date', 'end_date', 'thumbs']
ALCHEMY_API_KEY = None
RESULTS_DICT = dict([])
try:
    with open('alchemy_api.key', 'r') as f:
        ALCHEMY_API_KEY = f.read()
#except FileNotFoundError:
except IOError:
     LOG.info('WARNING: NO alchemy_api.key found, concept_tagging is NOT supported')


def _abort(code, msg, usage=True):
    if usage:
        msg += " " + _usage() + "'"

    response = jsonify(service_version=SERVICE_VERSION, msg=msg, code=code)
    response.status_code = code
    LOG.debug(str(response))

    return response


def _usage(joinstr="', '", prestr="'"):
    return 'Allowed request fields for ' + APOD_METHOD_NAME + ' method are ' + prestr + joinstr.join(
        ALLOWED_APOD_FIELDS)


def _validate(data):
    LOG.debug('_validate(data) called')
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True


def _validate_date(dt):
    LOG.debug('_validate_date(dt) called')
    today = datetime.today().date()
    begin = datetime(1995, 6, 16).date()  # first APOD image date

    # validate input
    if (dt > today) or (dt < begin):
        today_str = today.strftime('%b %d, %Y')
        begin_str = begin.strftime('%b %d, %Y')

        raise ValueError('Date must be between %s and %s.' % (begin_str, today_str))


def _apod_handler(dt, use_concept_tags=False, use_default_today_date=False, thumbs=False):
    """
    Accepts a parameter dictionary. Returns the response object to be
    served through the API.
    """
    try:
        
        page_props = parse_apod(dt, use_default_today_date, thumbs)
        if not page_props:
            return None
        LOG.debug('managed to get apod page characteristics')

        if use_concept_tags:
            if ALCHEMY_API_KEY is None:
                page_props['concepts'] = 'concept_tags functionality turned off in current service'
            else:
                page_props['concepts'] = get_concepts(request, page_props['explanation'], ALCHEMY_API_KEY)

        return page_props

    except Exception as e:

        LOG.error('Internal Service Error :' + str(type(e)) + ' msg:' + str(e))
        # return code 500 here
        return _abort(500, 'Internal Service Error', usage=False)


def _get_json_for_date(input_date, use_concept_tags, thumbs):
    """
    This returns the JSON data for a specific date, which must be a string of the form YYYY-MM-DD. If date is None,
    then it defaults to the current date.
    :param input_date:
    :param use_concept_tags:
    :return:
    """

    # get the date param
    use_default_today_date = False
    if not input_date:
        # fall back to using today's date IF they didn't specify a date
        use_default_today_date = True
        dt = input_date  # None
        key = datetime.utcnow().date()
        key = str(key.year)+'y'+str(key.month)+'m'+str(key.day)+'d'+str(use_concept_tags)+str(thumbs)

    # validate input date
    else:

        dt = datetime.strptime(input_date, '%Y-%m-%d').date()
        _validate_date(dt)
        key = str(dt.year)+'y'+str(dt.month)+'m'+str(dt.day)+'d'+str(use_concept_tags)+str(thumbs)

    # get data
    if key in RESULTS_DICT.keys():
        data = RESULTS_DICT[key]
    else:
        data = _apod_handler(dt, use_concept_tags, use_default_today_date, thumbs)
        

    # Handle case where no data is available
    if not data:
        return _abort(code=404, msg=f"No data available for date: {input_date}", usage=False)
    

    data['service_version'] = SERVICE_VERSION

    #Volatile caching dict
    datadate =  datetime.strptime(data['date'], '%Y-%m-%d').date()
    key = str(datadate.year)+'y'+str(datadate.month)+'m'+str(datadate.day)+'d'+str(use_concept_tags)+str(thumbs)
    RESULTS_DICT[key] = data


    # return info as JSON
    return jsonify(data)


def _get_json_for_random_dates(count, use_concept_tags, thumbs):
    """
    This returns the JSON data for a set of randomly chosen dates. The number of dates is specified by the count
    parameter
    :param count:
    :param use_concept_tags:
    :return:
    """
    if count > 100 or count <= 0:
        raise ValueError('Count must be positive and cannot exceed 100')
    begin_ordinal = datetime(1995, 6, 16).toordinal()
    today_ordinal = datetime.today().toordinal()

    random_date_ordinals = list(range(begin_ordinal, today_ordinal + 1))
    shuffle(random_date_ordinals)

    all_data = []
    for date_ordinal in random_date_ordinals:
        dt = date.fromordinal(date_ordinal)
        data = _apod_handler(dt, use_concept_tags, date_ordinal == today_ordinal, thumbs)
        
        # Handle case where no data is available
        if not data:
            continue

        data['service_version'] = SERVICE_VERSION
        all_data.append(data)
        if len(all_data) >= count:
            break

    return jsonify(all_data)


def _get_json_for_date_range(start_date, end_date, use_concept_tags, thumbs):
    """
    This returns the JSON data for a range of dates, specified by start_date and end_date, which must be strings of the
    form YYYY-MM-DD. If end_date is None then it defaults to the current date.
    :param start_date:
    :param end_date:
    :param use_concept_tags:
    :return:
    """
    # validate input date
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    _validate_date(start_dt)

    # get the date param
    if not end_date:
        # fall back to using today's date IF they didn't specify a date
        end_date = datetime.strftime(datetime.today(), '%Y-%m-%d')

    # validate input date
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    _validate_date(end_dt)

    start_ordinal = start_dt.toordinal()
    end_ordinal = end_dt.toordinal()
    today_ordinal = datetime.today().date().toordinal()

    if start_ordinal > end_ordinal:
        raise ValueError('start_date cannot be after end_date')

    all_data = []

    while start_ordinal <= end_ordinal:
        # get data
        dt = date.fromordinal(start_ordinal)
        
        data = _apod_handler(dt, use_concept_tags, start_ordinal == today_ordinal, thumbs)

        # Handle case where no data is available
        if not data:
            start_ordinal += 1
            continue

        data['service_version'] = SERVICE_VERSION

        if data['date'] == dt.isoformat():
            # Handles edge case where server is a day ahead of NASA APOD service
            all_data.append(data)

        start_ordinal += 1

    # return info as JSON
    return jsonify(all_data)


#
# Endpoints
#

@application.route('/')
def home():
    return render_template('home.html', version=SERVICE_VERSION,
                           service_url=request.host,
                           methodname=APOD_METHOD_NAME,
                           usage=_usage(joinstr='", "', prestr='"') + '"')

@application.route('/static/<asset_path>')
def serve_static(asset_path):
    return current_app.send_static_file(asset_path)


@application.route('/' + SERVICE_VERSION + '/' + APOD_METHOD_NAME + '/', methods=['GET'])
def apod():
    LOG.info('apod path called')
    try:

        # application/json GET method
        args = request.args

        if not _validate(args):
            return _abort(400, 'Bad Request: incorrect field passed.')

        #
        input_date = args.get('date')
        count = args.get('count')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        use_concept_tags = args.get('concept_tags', False)
        thumbs = args.get('thumbs', False)

        if not count and not start_date and not end_date:
            return _get_json_for_date(input_date, use_concept_tags, thumbs)

        elif not input_date and not start_date and not end_date and count:
            return _get_json_for_random_dates(int(count), use_concept_tags, thumbs)

        elif not count and not input_date and start_date:
            return _get_json_for_date_range(start_date, end_date, use_concept_tags, thumbs)

        else:
            return _abort(400, 'Bad Request: invalid field combination passed.')

    except ValueError as ve:
        return _abort(400, str(ve), False)

    except Exception as ex:

        etype = type(ex)
        if etype == ValueError or 'BadRequest' in str(etype):
            return _abort(400, str(ex) + ".")
        else:
            LOG.error('Service Exception. Msg: ' + str(type(ex)))
            return _abort(500, 'Internal Service Error', usage=False)


@application.errorhandler(404)
def page_not_found(e):
    """
    Return a custom 404 error.
    """
    LOG.info('Invalid page request: ' + str(e))
    return _abort(404, 'Sorry, Nothing at this URL.', usage=True)


@application.errorhandler(500)
def application_error(e):
    """
    Return a custom 500 error.
    """
    return _abort(500, 'Sorry, unexpected error: {}'.format(e), usage=False)


if __name__ == '__main__':
    application.run('0.0.0.0', port=5000)
