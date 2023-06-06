# Astronomy Picture of the Day (APOD) microservice

A microservice written in Python with the [Flask micro framework](http://flask.pocoo.org).

## NOTES: 
### Code re-organization has occurred [2020-05-04]!
Code was reorganized to make it work more easily on AWS's Elastic Beanstalk service.

The changes over previous version were :
1. Moved main code out of the APOD folder and into the top level directory as Elastic Beanstalk had a hard time finding the initial python file unless it was in the top-level folder. 
2. Changed service.py to application.py
3. Changed references to app in application.py to application

You can find a frozen version of the previous code in the branch called <a href="https://github.com/nasa/apod-api/tree/prevCodeOrganization">"prevCodeOrganization"</a>

#### API Reliability
A very large number of people use the instance of this API that NASA has set up. If you need a extremely reliable version of this API, you likely want to stand up your own version of the API. You can do that with this code! All information that this API returns is actually just grabbed from the <a href='https://apod.nasa.gov/apod/astropix.html'>Astronomy Photo of the Day Website</a> (APOD).

#### Content Related Issues
No one watching this repository has anything to do with Astronomy Photo of the Day website, so we're unable to deal with issues directly related to their content. Please contact them directly.


# Table of contents
1. [Getting Started](#getting_started)
    1. [Standard environment](#standard_env)
    2. [`virtualenv` environment](#virtualenv)
    3. [`conda` environment](#conda)
2. [Docs](#docs)
3. [APOD parser](#TheAPODParser)
4. [Deployed](#Deployed)
5. [Feedback](#feedback)
6. [Author](#author)

&nbsp;
## Getting started <a name="getting_started"></a>

### Standard environment <a name="standard_env"></a>

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Install dependencies into the project's `lib`
```bash
pip install -r requirements.txt -t lib
```
4. Add `lib` to your PYTHONPATH and run the server
```bash
PYTHONPATH=./lib python application.py
```
&nbsp;
### `virtualenv` environment <a name="virtualenv"></a>

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Create a new virtual environment `env` in the directory
```bash
python -m venv venv
```
4. Activate the new environment
```bash
.\venv\Scripts\Activate
```
5. Install dependencies in new environment
```bash
pip install -r requirements.txt
```
6. Run the server locally
```bash
python application.py
```
&nbsp;
### `conda` environment <a name="conda"></a>

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Create a new virtual environment `env` in the directory
```bash
conda create --prefix ./env
```
4. Activate the new environment
```bash
conda activate ./env
```
5. Install dependencies in new environment
```bash
pip install -r requirements.txt
```
6. Run the server locally
```bash
python application.py
```

### Run it in Docker

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api.git
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Build the image
```bash
docker build . -t apod-api
```
4. Run the image
```bash
docker run -p 5000:5000 apod-api
```

&nbsp;
## Docs <a name="docs"></a>

### Endpoint: `/<version>/apod`

There is only one endpoint in this service which takes 2 optional fields
as parameters to a http GET request. A JSON dictionary is returned nominally.

#### URL Search Params | query string parameters

- `api_key` | demo: `DEMO_KEY` | https://api.nasa.gov/#signUp
- `date` A string in YYYY-MM-DD format indicating the date of the APOD image (example: 2014-11-03).  Defaults to today's date.  Must be after 1995-06-16, the first day an APOD picture was posted.  There are no images for tomorrow available through this API.
- `concept_tags` A boolean `True|False` indicating whether concept tags should be returned with the rest of the response.  The concept tags are not necessarily included in the explanation, but rather derived from common search tags that are associated with the description text.  (Better than just pure text search.)  Defaults to False.
- `hd` A boolean `True|False` parameter indicating whether or not high-resolution images should be returned. This is present for legacy purposes, it is always ignored by the service and high-resolution urls are returned regardless.
- `count` A positive integer, no greater than 100. If this is specified then `count` randomly chosen images will be returned in a JSON array. Cannot be used in conjunction with `date` or `start_date` and `end_date`.
- `start_date` A string in YYYY-MM-DD format indicating the start of a date range. All images in the range from `start_date` to `end_date` will be returned in a JSON array. Cannot be used with `date`.
- `end_date` A string in YYYY-MM-DD format indicating that end of a date range. If `start_date` is specified without an `end_date` then `end_date` defaults to the current date.
- `thumbs` A boolean parameter `True|False` inidcating whether the API should return a thumbnail image URL for video files. If set to `True`, the API returns URL of video thumbnail. If an APOD is not a video, this parameter is ignored.

**Returned fields**

- `resource` A dictionary describing the `image_set` or `planet` that the response illustrates, completely determined by the structured endpoint.
- `concept_tags` A boolean reflection of the supplied option.  Included in response because of default values.
- `title` The title of the image.
- `date` Date of image. Included in response because of default values.
- `url` The URL of the APOD image or video of the day.
- `hdurl` The URL for any high-resolution image for that day. Returned regardless of 'hd' param setting but will be omitted in the response IF it does not exist originally at APOD.
- `media_type` The type of media (data) returned. May either be 'image' or 'video' depending on content.
- `explanation` The supplied text explanation of the image.
- `concepts` The most relevant concepts within the text explanation.  Only supplied if `concept_tags` is set to True.
- `thumbnail_url` The URL of thumbnail of the video. 
- `copyright` The name of the copyright holder.
- `service_version` The service version used.

**Example**

```bash
localhost:5000/v1/apod?api_key=DEMO_KEY&date=2014-10-01&concept_tags=True
```
<details><summary>See Return Object</summary>
<p>

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

</p>
</details>


```bash
https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=5
```

<details><summary>See Return Object</summary>
<p>


```jsoniq
[
  {
    "copyright": "Panther Observatory",
    "date": "2006-04-15",
    "explanation": "In this stunning cosmic vista, galaxy M81 is on the left surrounded by blue spiral arms.  On the right marked by massive gas and dust clouds, is M82.  These two mammoth galaxies have been locked in gravitational combat for the past billion years.   The gravity from each galaxy dramatically affects the other during each hundred million-year pass.  Last go-round, M82's gravity likely raised density waves rippling around M81, resulting in the richness of M81's spiral arms.  But M81 left M82 with violent star forming regions and colliding gas clouds so energetic the galaxy glows in X-rays.  In a few billion years only one galaxy will remain.",
    "hdurl": "https://apod.nasa.gov/apod/image/0604/M81_M82_schedler_c80.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Galaxy Wars: M81 versus M82",
    "url": "https://apod.nasa.gov/apod/image/0604/M81_M82_schedler_c25.jpg"
  },
  {
    "date": "2013-07-22",
    "explanation": "You are here.  Everyone you've ever known is here. Every human who has ever lived -- is here. Pictured above is the Earth-Moon system as captured by the Cassini mission orbiting Saturn in the outer Solar System. Earth is the brighter and bluer of the two spots near the center, while the Moon is visible to its lower right. Images of Earth from Saturn were taken on Friday. Quickly released unprocessed images were released Saturday showing several streaks that are not stars but rather cosmic rays that struck the digital camera while it was taking the image.  The above processed image was released earlier today.  At nearly the same time, many humans on Earth were snapping their own pictures of Saturn.   Note: Today's APOD has been updated.",
    "hdurl": "https://apod.nasa.gov/apod/image/1307/earthmoon2_cassini_946.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Earth and Moon from Saturn",
    "url": "https://apod.nasa.gov/apod/image/1307/earthmoon2_cassini_960.jpg"
  },
  {
    "copyright": "Joe Orman",
    "date": "2000-04-06",
    "explanation": "Rising before the Sun on February 2nd, astrophotographer Joe Orman anticipated this apparition of the bright morning star Venus near a lovely crescent Moon above a neighbor's house in suburban Phoenix, Arizona, USA. Fortunately, the alignment of bright planets and the Moon is one of the most inspiring sights in the night sky and one that is often easy to enjoy and share without any special equipment. Take tonight, for example. Those blessed with clear skies can simply step outside near sunset and view a young crescent Moon very near three bright planets in the west Jupiter, Mars, and Saturn. Jupiter will be the unmistakable brightest star near the Moon with a reddish Mars just to Jupiter's north and pale yellow Saturn directly above. Of course, these sky shows create an evocative picture but the planets and Moon just appear to be near each other -- they are actually only approximately lined up and lie in widely separated orbits. Unfortunately, next month's highly publicized alignment of planets on May 5th will be lost from view in the Sun's glare but such planetary alignments occur repeatedly and pose no danger to planet Earth.",
    "hdurl": "https://apod.nasa.gov/apod/image/0004/vm_orman_big.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Venus, Moon, and Neighbors",
    "url": "https://apod.nasa.gov/apod/image/0004/vm_orman.jpg"
  },
  {
    "date": "2014-07-12",
    "explanation": "A new star, likely the brightest supernova in recorded human history, lit up planet Earth's sky in the year 1006 AD. The expanding debris cloud from the stellar explosion, found in the southerly constellation of Lupus, still puts on a cosmic light show across the electromagnetic spectrum. In fact, this composite view includes X-ray data in blue from the Chandra Observatory, optical data in yellowish hues, and radio image data in red. Now known as the SN 1006 supernova remnant, the debris cloud appears to be about 60 light-years across and is understood to represent the remains of a white dwarf star. Part of a binary star system, the compact white dwarf gradually captured material from its companion star. The buildup in mass finally triggered a thermonuclear explosion that destroyed the dwarf star. Because the distance to the supernova remnant is about 7,000 light-years, that explosion actually happened 7,000 years before the light reached Earth in 1006. Shockwaves in the remnant accelerate particles to extreme energies and are thought to be a source of the mysterious cosmic rays.",
    "hdurl": "https://apod.nasa.gov/apod/image/1407/sn1006c.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "SN 1006 Supernova Remnant",
    "url": "https://apod.nasa.gov/apod/image/1407/sn1006c_c800.jpg"
  },
  {
    "date": "1997-01-21",
    "explanation": "In Jules Verne's science fiction classic A Journey to the Center of the Earth, Professor Hardwigg and his fellow explorers encounter many strange and exciting wonders. What wonders lie at the center of our Galaxy? Astronomers now know of some of the bizarre objects which exist there, like vast dust clouds,\r bright young stars, swirling rings of gas, and possibly even a large black hole. Much of the Galactic center region is shielded from our view in visible light by the intervening dust and gas. But it can be explored using other forms of electromagnetic radiation, like radio, infrared, X-rays, and gamma rays. This beautiful high resolution image of the Galactic center region in infrared light was made by the SPIRIT III telescope onboard the Midcourse Space Experiment. The center itself appears as a bright spot near the middle of the roughly 1x3 degree field of view, the plane of the Galaxy is vertical, and the north galactic pole is towards the right. The picture is in false color - starlight appears blue while dust is greenish grey, tending to red in the cooler areas.",
    "hdurl": "https://apod.nasa.gov/apod/image/9701/galcen_msx_big.gif",
    "media_type": "image",
    "service_version": "v1",
    "title": "Journey to the Center of the Galaxy \r\nCredit:",
    "url": "https://apod.nasa.gov/apod/image/9701/galcen_msx.jpg"
  }
]
```

</p>
</details>



```bash
https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&start_date=2017-07-08&end_date=2017-07-10
```

<details><summary>See Return Object</summary>
<p>

```jsoniq
[
  {
    "copyright": "T. Rector",
    "date": "2017-07-08",
    "explanation": "Similar in size to large, bright spiral galaxies in our neighborhood, IC 342 is a mere 10 million light-years distant in the long-necked, northern constellation Camelopardalis. A sprawling island universe, IC 342 would otherwise be a prominent galaxy in our night sky, but it is hidden from clear view and only glimpsed through the veil of stars, gas and dust clouds along the plane of our own Milky Way galaxy. Even though IC 342's light is dimmed by intervening cosmic clouds, this sharp telescopic image traces the galaxy's own obscuring dust, blue star clusters, and glowing pink star forming regions along spiral arms that wind far from the galaxy's core. IC 342 may have undergone a recent burst of star formation activity and is close enough to have gravitationally influenced the evolution of the local group of galaxies and the Milky Way.",
    "hdurl": "https://apod.nasa.gov/apod/image/1707/ic342_rector2048.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Hidden Galaxy IC 342",
    "url": "https://apod.nasa.gov/apod/image/1707/ic342_rector1024s.jpg"
  },
  {
    "date": "2017-07-09",
    "explanation": "Can you find your favorite country or city?  Surprisingly, on this world-wide nightscape, city lights make this task quite possible.  Human-made lights highlight particularly developed or populated areas of the Earth's surface, including the seaboards of Europe, the eastern United States, and Japan.  Many large cities are located near rivers or oceans so that they can exchange goods cheaply by boat.  Particularly dark areas include the central parts of South America, Africa, Asia, and Australia.  The featured composite was created from images that were collected during cloud-free periods in April and October 2012 by the Suomi-NPP satellite, from a polar orbit about 824 kilometers above the surface, using its Visible Infrared Imaging Radiometer Suite (VIIRS).",
    "hdurl": "https://apod.nasa.gov/apod/image/1707/EarthAtNight_SuomiNPP_3600.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Earth at Night",
    "url": "https://apod.nasa.gov/apod/image/1707/EarthAtNight_SuomiNPP_1080.jpg"
  },
  {
    "date": "2017-07-10",
    "explanation": "What's happening around the center of this spiral galaxy? Seen in total, NGC 1512 appears to be a barred spiral galaxy -- a type of spiral that has a straight bar of stars across its center.  This bar crosses an outer ring, though, a ring not seen as it surrounds the pictured region. Featured in this Hubble Space Telescope image is an inner ring -- one that itself surrounds the nucleus of the spiral.  The two rings are connected not only by a bar of bright stars but by dark lanes of dust. Inside of this inner ring, dust continues to spiral right into the very center -- possibly the location of a large black hole. The rings are bright with newly formed stars which may have been triggered by the collision of NGC 1512 with its galactic neighbor, NGC 1510.",
    "hdurl": "https://apod.nasa.gov/apod/image/1707/NGC1512_Schmidt_1342.jpg",
    "media_type": "image",
    "service_version": "v1",
    "title": "Spiral Galaxy NGC 1512: The Nuclear Ring",
    "url": "https://apod.nasa.gov/apod/image/1707/NGC1512_Schmidt_960.jpg"
  }
]
```


</p>
</details>

#### Copyright
If you are re-displaying imagery, you may want to check for the presence of the copyright. Anything without a copyright returned field is generally NASA and in the public domain. Please see the <a href=https://apod.nasa.gov/apod/lib/about_apod.html>"About image permissions"</a> section on the main Astronomy Photo of the Day site for more information.

## The APOD Parser<a name="TheAPODParser"></a>

<i>The APOD Parser is not part of the API itself. </i> Rather is intended to be used for accessing the APOD API quickly with Python without writing much additional code yourself. It is found in the apod_parser folder.

### Usage

1. First import the `apod_object_parser.py` file.

2. Now use the `get_data` function and pass your API key as the only argument. You can get the API key <a href="https://api.nasa.gov/#signUp">here</a>

```python
response = apod_object_parser.get_data(<your_api_key>)
```

3. Now you can use the following functions:

-> `apod_object_parser.get_date(response)`

-> `apod_object_parser.get_explaination(response)`

-> `apod_object_parser.get_hdurl(response)`

-> `apod_object_parser.get_media_type(response)`

-> `apod_object_parser.get_service_version(response)`

-> `apod_object_parser.get_title(response)`

-> `apod_object_parser.get_url(response)`

**for full docs and more functions visit the readme of  the apod parser by clicking <a href="apod_parser/apod_parser_readme.md">here</a>**

## Deployed <a name="Deployed"></a>
The deployed version of this API is based on the `eb` branch. The version that was deployed before that is in the `eb_previous` branch. The `master` branch is used as development as that's where most of the pull requests will come into anyways.

This API is deployed on AWS using elastic beanstalk due to large number of people who use the service. However, if you're planning on using it just yourself, it is small enough to be stood up on a single micro EC2 or any other small size cloud compute machine.

## Feedback <a name="feedback"></a>

Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Author <a name="author"></a>
- Brian Thomas (based on code by Dan Hammer) 
- Justin Gosses (made changes to allow this repository to run more easily on AWS Elastic Beanstalk after heroku instance was shut-down)
- Please checkout the <a href="https://github.com/nasa/apod-api/graphs/contributors">contributers</a> to this repository on the righthand side of this page. 

## Contributing
We do accept pull requests from the public. Please note that we can be slow to respond. Please be patient. 

Also, **the people with rights on this repository are not people who can debug problems with the APOD website itself**. If you would like to contribute, right now we could use some attention to the tests. 

## Links

- [YouTube Embedded Players and Player Parameters](https://developers.google.com/youtube/player_parameters)
