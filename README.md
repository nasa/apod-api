# Astronomy Picture of the Day (APOD) microservice

A microservice written in Python which may be run on Google App 
Engine with the [Flask micro framework](http://flask.pocoo.org).


## Endpoint: `/<version>/apod`

There is only one endpoint in this service which takes 2 optional fields
as parameters to a http GET request. A JSON dictionary is returned nominally. 

**Fields**

- `date` A string in YYYY-MM-DD format indicating the date of the APOD image (example: 2014-11-03).  Defaults to today's date.  Must be after 1995-06-16, the first day an APOD picture was posted.  There are no images for tomorrow available through this API.
- `concept_tags` A boolean indicating whether concept tags should be returned with the rest of the response.  The concept tags are not necessarily included in the explanation, but rather derived from common search tags that are associated with the description text.  (Better than just pure text search.)  Defaults to False.
- `hd` A boolean parameter indicating whether or not high-resolution images should be returned. This is present for legacy purposes, it is always ignored by the service and high-resolution urls are returned regardless.

**Returned fields**

- `resource` A dictionary describing the `image_set` or `planet` that the response illustrates, completely determined by the structured endpoint.
- `concept_tags` A boolean reflection of the supplied option.  Included in response because of default values.
- `title` The title of the image.
- `date` Date of image. Included in response because of default values.
- `url` The URL of the APOD image or video of the day.
- `hdurl` The URL for any high-resolution image for that day. Returned regardless of 'hd' param setting but will be ommited in the response IF it does not exist originally at APOD.
- `media_type` The type of media (data) returned. May either be 'image' or 'video' depending on content.
- `explanation` The supplied text explanation of the image.
- `concepts` The most relevant concepts within the text explanation.  Only supplied if `concept_tags` is set to True.

**Example**

```bash
localhost:5000/v1/apod?date=2014-10-01&concept_tags=True
```

```jsoniq
{
    resource: {
        image_set: "apod"
    },
    concept_tags: "True",
    date: "2013-10-01", 
    title: "Filaments of the Vela Supernova Remnant",
    url: "http://apod.nasa.gov/apod/image/1310/velafilaments_jadescope_960.jpg",
    explanation: "The explosion is over but the consequences continue. About eleven
    thousand years ago a star in the constellation of Vela could be seen to explode,
    creating a strange point of light briefly visible to humans living near the 
    beginning of recorded history. The outer layers of the star crashed into the 
    interstellar medium, driving a shock wave that is still visible today. A roughly 
    spherical, expanding shock wave is visible in X-rays. The above image captures some
    of that filamentary and gigantic shock in visible light. As gas flies away from the
    detonated star, it decays and reacts with the interstellar medium, producing light
    in many different colors and energy bands. Remaining at the center of the Vela
    Supernova Remnant is a pulsar, a star as dense as nuclear matter that rotates
    completely around more than ten times in a single second.",
    concepts: {
        0: "Astronomy",
        1: "Star",
        2: "Sun",
        3: "Milky Way",
        4: "Hubble Space Telescope",
        5: "Earth",
        6: "Nebula",
        7: "Interstellar medium"
    }
}
```

## Getting started

1. Install the [App Engine Python SDK](https://developers.google.com/appengine/downloads).

This API runs on Google App Engine.  It's not an easy development environment, especially when compared against to lightweight Flask APIs.  But scaling in production is amazingly simple.  The setup is non-trivial but it's worth it.  

I would encourage installing App Engine via [Google Cloud SDK](https://cloud.google.com/sdk/).  It's included in the install.
```bash
curl https://sdk.cloud.google.com | bash
```
Follow the install prompts at the command line and then restart your terminal (or just `source .bash_profile` or `source .bashrc`).  Then type the following to authenticate.
```bash
gcloud auth login
```

See the README file for directions. 
You'll need python 2.7 and [pip 1.4 or later](http://www.pip-installer.org/en/latest/installing.html) installed too..

2. Clone this repo with

   ```
   git clone https://github.com/nasa/apod-api.git
   ```

3. Install dependencies in the project's lib directory.
   Note: App Engine can only import libraries from inside your project directory.

   ```
   cd apod-api
   pip install -r requirements.txt -t lib
   ```

4. Optional: obtain a key from http://alchemyapi.com an deposit that file
   in the file 'alchemy_api.key'. This supports the concept_tags functionality
   of this service.

   IMPORTANT: under NO circumstances should you check in the actual instance of the key into the repository.

5. To run this project locally from the command line:

   ```
   dev_appserver.py .
   ```

Visit the application [http://localhost:8080](http://localhost:8080)

See [the development server documentation](https://developers.google.com/appengine/docs/python/tools/devserver)
for options when running dev_appserver.

## Deploy

To deploy the application:

1. Use the [Admin Console](https://appengine.google.com) to create a
   project/app id. (App id and project id are identical)
1. [Deploy the
   application](https://developers.google.com/appengine/docs/python/tools/uploadinganapp) with

   ```
   appcfg.py -A apod-api update .
   ```
1. Congratulations!  Your application is now live at apod-api.appspot.com

### Installing Libraries
See the [Third party
libraries](https://developers.google.com/appengine/docs/python/tools/libraries27)
page for libraries that are already included in the SDK.  To include SDK
libraries, add them in your app.yaml file. Other than libraries included in
the SDK, only pure python libraries may be added to an App Engine project.

### Feedback
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Licensing
See [LICENSE](LICENSE)

## Author
Brian Thomas (based on code by Dan Hammer) 

