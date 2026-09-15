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

@author=dcrendon @email=daniel.c.rendon@nasa.gov
"""

import logging
from datetime import date, datetime

import requests
from flask import Flask, current_app, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {"expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining"]}
    },
)

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# this should reflect both this service and the backing
# assorted libraries
SERVICE_VERSION = "v1"
APOD_METHOD_NAME = "apod"
ALLOWED_APOD_FIELDS = [
    "concept_tags",
    "date",
    "hd",
    "count",
    "start_date",
    "end_date",
    "thumbs",
]
ALCHEMY_API_KEY = None
RESULTS_DICT = dict([])
try:
    with open("alchemy_api.key", "r") as f:
        ALCHEMY_API_KEY = f.read()
# except FileNotFoundError:
except IOError:
    LOG.info("WARNING: NO alchemy_api.key found, concept_tagging is NOT supported")


def _abort(code, msg, usage=True):
    if usage:
        msg += " " + _usage() + "'"

    response = jsonify(service_version=SERVICE_VERSION, msg=msg, code=code)
    response.status_code = code
    LOG.debug(str(response))

    return response


def _usage(joinstr="', '", prestr="'"):
    return (
        "Allowed request fields for "
        + APOD_METHOD_NAME
        + " method are "
        + prestr
        + joinstr.join(ALLOWED_APOD_FIELDS)
    )


def _validate(data):
    LOG.debug("_validate(data) called")
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True


def _gen_date_after_date(start_date: datetime) -> datetime:
    import random
    from datetime import timedelta

    today = date.today()
    days_difference = (today - start_date).days
    random_days = random.randrange(1, days_difference)
    random_future_date = start_date + timedelta(days=random_days)
    return random_future_date


def _get_json_for_date(input_date):
    """
    This returns the JSON data for a specific date, which must be a string of the form YYYY-MM-DD. If date is None,
    then it defaults to the current date.
    :param input_date:
    :param use_concept_tags:
    :param thumbs:
    :return:
    """

    # get the date param
    data = requests.get(
        f"https://science.nasa.gov/wp-json/wp/v2/apod-basic/{input_date}"
    )
    if data.status_code != 200:
        return None
    json_response = data.json()
    json_response.setdefault("url", json_response.get("hdurl"))
    json_response["service_version"] = SERVICE_VERSION

    # return info as JSON
    return json_response


def _get_json_for_random_dates(count):
    """
    This returns the JSON data for a set of randomly chosen dates. The number of dates is specified by the count
    parameter
    :param count:
    :param use_concept_tags:
    :return:
    """
    if count > 25 or count <= 0:
        raise ValueError("Count must be positive and cannot exceed 25")

    all_data = []
    attempts = 0
    max_attempts = count * 3  # cap so a down upstream returns fewer, never hangs
    while len(all_data) < count and attempts < max_attempts:
        attempts += 1
        rand_date = _gen_date_after_date(date(1995, 6, 16))
        format_date = str(rand_date).replace("-", "")[2:]
        data = requests.get(
            f"https://science.nasa.gov/wp-json/wp/v2/apod-basic/{format_date}"
        )

        # Handle case where no data is available: retry with another date
        if data.status_code != 200:
            continue

        json_response = data.json()
        json_response.setdefault("url", json_response.get("hdurl"))
        json_response["service_version"] = SERVICE_VERSION

        all_data.append(json_response)

    return jsonify(all_data)


def _get_json_for_date_range(start_date, end_date):
    """
    This returns the JSON data for a range of dates, specified by start_date and end_date, which must be strings of the
    form YYYY-MM-DD. If end_date is None then it defaults to the current date.
    :param start_date:
    :param end_date:
    :param use_concept_tags:
    :return:
    """

    # validate input date
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    # get the date param
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")

    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    if start_dt > end_dt:
        raise ValueError("start_date cannot be after end_date")

    use_start_date = str(start_date).replace("-", "")[2:]
    use_end_date = str(end_date).replace("-", "")[2:]
    base_url = f"https://science.nasa.gov/wp-json/wp/v2/apod-basic?date_from={use_start_date}&date_to={use_end_date}"

    all_data = []
    seen_dates = set()
    page = 1
    while True:
        data = requests.get(f"{base_url}&page={page}")
        if data.status_code != 200:
            break
        json_response = data.json()
        if not isinstance(json_response, list) or not json_response:
            break

        # the upstream endpoint ignores unknown query parameters: when asked for
        # a page beyond its results it repeats page 1 — stop instead of duplicating
        page_dates = {item.get("date") for item in json_response}
        if page > 1 and page_dates & seen_dates:
            break
        seen_dates |= page_dates

        for item in json_response:
            item.setdefault("url", item.get("hdurl"))
            item["service_version"] = SERVICE_VERSION
        all_data.extend(json_response)
        page += 1

    # return info as JSON
    return all_data


#
# Endpoints
#


@app.route("/")
def home():
    return render_template(
        "home.html",
        version=SERVICE_VERSION,
        service_url=request.host,
        methodname=APOD_METHOD_NAME,
        usage=_usage(joinstr='", "', prestr='"') + '"',
    )


@app.route("/static/<asset_path>")
def serve_static(asset_path):
    return current_app.send_static_file(asset_path)


@app.route("/" + SERVICE_VERSION + "/" + APOD_METHOD_NAME + "/", methods=["GET"])
def apod():
    try:
        # app/json GET method
        args = request.args
        if not _validate(args):
            return _abort(400, "Bad Request: incorrect field passed.")

        input_date = args.get("date", "")  # use legacy date format

        count = args.get("count", "")

        start_date = args.get("start_date", "")  # date_from - remove dashes
        end_date = args.get("end_date", "")  # date_to - remove dashes

        if not count and not start_date and not end_date:
            if not input_date:
                input_date = date.today().strftime("%y%m%d")
            if "-" in input_date:
                input_date = str(input_date).replace("-", "")[2:]
            result = _get_json_for_date(input_date)
            if result is None:
                return _abort(
                    400,
                    f"Bad Request: no APOD entry found for date '{input_date}'.",
                    False,
                )
            return result

        elif not input_date and not start_date and not end_date and count:
            return _get_json_for_random_dates(int(count))

        elif not count and not input_date and start_date:
            return _get_json_for_date_range(start_date, end_date)

        else:
            return _abort(400, "Bad Request: invalid field combination passed.")

    except ValueError as ve:
        return _abort(400, str(ve), False)

    except Exception as ex:
        etype = type(ex)
        if etype is ValueError or "BadRequest" in str(etype):
            return _abort(400, str(ex) + ".")
        else:
            LOG.error("Service Exception. Msg: " + str(type(ex)))
            return _abort(500, "Internal Service Error", usage=False)


@app.errorhandler(404)
def page_not_found(e):
    """
    Return a custom 404 error.
    """
    LOG.info("Invalid page request: " + str(e))
    return _abort(404, "Sorry, Nothing at this URL.", usage=True)


@app.errorhandler(500)
def app_error(e):
    """
    Return a custom 500 error.
    """
    return _abort(500, "Sorry, unexpected error: {}".format(e), usage=False)


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
