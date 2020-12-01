#!/bin/sh/python
# coding= utf-8 
import unittest
from apod import utility 
import logging

logging.basicConfig(level=logging.DEBUG)

from datetime import datetime
class TestApod(unittest.TestCase):
    """Test the extraction of APOD characteristics."""
    
    TEST_DATA = { 
        'normal page, copyright' :
        {
            "datetime": datetime(2017, 3, 22),
            "copyright": 'Robert Gendler',
            "date": "2017-03-22", 
            "explanation": "In cosmic brush strokes of glowing hydrogen gas, this beautiful skyscape unfolds across the plane of our Milky Way Galaxy near the northern end of the Great Rift and the center of the constellation Cygnus the Swan. A 36 panel mosaic of telescopic image data, the scene spans about six degrees. Bright supergiant star Gamma Cygni (Sadr) to the upper left of the image center lies in the foreground of the complex gas and dust clouds and crowded star fields. Left of Gamma Cygni, shaped like two luminous wings divided by a long dark dust lane is IC 1318 whose popular name is understandably the Butterfly Nebula. The more compact, bright nebula at the lower right is NGC 6888, the Crescent Nebula. Some distance estimates for Gamma Cygni place it at around 1,800 light-years while estimates for IC 1318 and NGC 6888 range from 2,000 to 5,000 light-years.", 
            "hdurl": "https://apod.nasa.gov/apod/image/1703/Cygnus-New-L.jpg", 
            "media_type": "image", 
            "service_version": "v1", 
            "title": "Central Cygnus Skyscape", 
            "url": "https://apod.nasa.gov/apod/image/1703/Cygnus-New-1024.jpg", 
        },
        'newer page, Reprocessing & copyright' :  
        {
            "datetime": datetime(2017, 2, 8),
            "copyright": "Jes�s M.Vargas & Maritxu Poyal",
            "date": "2017-02-08",
            "explanation": "The bright clusters and nebulae of planet Earth's night sky are often named for flowers or insects. Though its wingspan covers over 3 light-years, NGC 6302 is no exception. With an estimated surface temperature of about 250,000 degrees C, the dying central star of this particular planetary nebula has become exceptionally hot, shining brightly in ultraviolet light but hidden from direct view by a dense torus of dust.  This sharp close-up of the dying star's nebula was recorded by the Hubble Space Telescope and is presented here in reprocessed colors.  Cutting across a bright cavity of ionized gas, the dust torus surrounding the central star is near the center of this view, almost edge-on to the line-of-sight. Molecular hydrogen has been detected in the hot star's dusty cosmic shroud. NGC 6302 lies about 4,000 light-years away in the arachnologically correct constellation of the Scorpion (Scorpius).   Follow APOD on: Facebook,  Google Plus,  Instagram, or Twitter",
            "hdurl": "https://apod.nasa.gov/apod/image/1702/Butterfly_HubbleVargas_5075.jpg",
            "media_type": "image",
            "service_version": "v1",
            "title": "The Butterfly Nebula from Hubble",
            "url": "https://apod.nasa.gov/apod/image/1702/Butterfly_HubbleVargas_960.jpg"
        }, 
        'older page, copyright' :  
        {
            "datetime": datetime(2015, 11, 15),
            "copyright": "Sean M. Sabatini",
            "date": "2015-11-15",
            "explanation": "There was a shower over Monument Valley -- but not water.  Meteors.  The featured image -- actually a composite of six exposures of about 30 seconds each -- was taken in 2001, a year when there was a very active Leonids shower. At that time, Earth was moving through a particularly dense swarm of sand-sized debris from Comet Tempel-Tuttle, so that meteor rates approached one visible streak per second. The meteors appear parallel because they all fall to Earth from the meteor shower radiant -- a point on the sky towards the constellation of the Lion (Leo). The yearly Leonids meteor shower peaks again this week. Although the Moon's glow should not obstruct the visibility of many meteors, this year's shower will peak with perhaps 15 meteors visible in an hour, a rate which is good but not expected to rival the 2001 Leonids.  By the way -- how many meteors can you identify in the featured image?",
            "hdurl": "https://apod.nasa.gov/apod/image/1511/leonidsmonuments_sabatini_2330.jpg",
            "media_type": "image",
            "service_version": "v1",
            "title": "Leonids Over Monument Valley",
            "url": "https://apod.nasa.gov/apod/image/1511/leonidsmonuments_sabatini_960.jpg"
        }, 
        'older page, copyright #2' :  
        {
            "datetime": datetime(2013, 3, 11),
            # this illustrates problematic, but still functional parsing of the copyright 
            "copyright": 'Martin RietzeAlien Landscapes on Planet Earth',
            "date": "2013-03-11",
            "explanation": "Why does a volcanic eruption sometimes create lightning? Pictured above, the Sakurajima volcano in southern Japan was caught erupting in early January. Magma bubbles so hot they glow shoot away as liquid rock bursts through the Earth's surface from below.  The above image is particularly notable, however, for the lightning bolts caught near the volcano's summit.  Why lightning occurs even in common thunderstorms remains a topic of research, and the cause of volcanic lightning is even less clear. Surely, lightning bolts help quench areas of opposite but separated electric charges. One hypothesis holds that catapulting magma bubbles or volcanic ash are themselves electrically charged, and by their motion create these separated areas. Other volcanic lightning episodes may be facilitated by charge-inducing collisions in volcanic dust. Lightning is usually occurring somewhere on Earth, typically over 40 times each second.",
            "hdurl": "https://apod.nasa.gov/apod/image/1303/volcano_reitze_1280.jpg",
            "media_type": "image",
            "service_version": "v1",
            "title": "Sakurajima Volcano with Lightning",
            "url": "https://apod.nasa.gov/apod/image/1303/volcano_reitze_960.jpg"
        }, 
        'older page, no copyright' :  
        {
            "datetime": datetime(1998, 6, 19),
            "date": "1998-06-19",
            "copyright": None,
            "explanation": "Looking down on the Northern Hemisphere of Mars on June 1, the Mars Global Surveyor spacecraft's wide angle camera recorded this morning image of the red planet. Mars Global Surveyor's orbit is now oriented to view the planet's surface during the morning hours and the night/day shadow boundary or terminator arcs across the left side of the picture. Two large volcanos, Olympus Mons (left of center) and Ascraeus Mons (lower right) peer upward through seasonal haze and water-ice clouds of the Northern Martian Winter. The color image was synthesized from red and blue band pictures and only approximates a \"true color\" picture of Mars.",
            "hdurl": "https://apod.nasa.gov/apod/image/9806/tharsis_mgs_big.jpg",
            "media_type": "image",
            "service_version": "v1",
            "title": "Good Morning Mars",
            "url": "https://apod.nasa.gov/apod/image/9806/tharsis_mgs.jpg"
        },
        'older page, no copyright, #2' :  
        {
            "datetime": datetime(2012, 8, 30),
            "date": "2012-08-30",
            "copyright": None,
            "explanation": "Have you seen a panorama from another world lately? Assembled from high-resolution scans of the original film frames, this one sweeps across the magnificent desolation of the Apollo 11 landing site on the Moon's Sea of Tranquility. Taken by Neil Armstrong looking out his window of the Eagle Lunar Module, the frame at the far left (AS11-37-5449) is the first picture taken by a person on another world. Toward the south, thruster nozzles can be seen in the foreground on the left, while at the right, the shadow of the Eagle is visible toward the west. For scale, the large, shallow crater on the right has a diameter of about 12 meters. Frames taken from the Lunar Module windows about an hour and a half after landing, before walking on the lunar surface, were intended to initially document the landing site in case an early departure was necessary.",
            "hdurl": "https://apod.nasa.gov/apod/image/1208/a11pan1040226lftsm.jpg",
            "media_type": "image",
            "service_version": "v1",
            "title": "Apollo 11 Landing Site Panorama",
            "url": "https://apod.nasa.gov/apod/image/1208/a11pan1040226lftsm600.jpg"
        },
    }
    
    def _test_harness(self, test_title, data):
        
        print ("Testing "+test_title)
               
        # make the call
        values = utility.parse_apod(data['datetime'])

        # Test returned properties
        for prop in values.keys(): 
            if prop == "copyright":
                print(str(values['copyright']))
            self.assertEqual(values[prop], data[prop], "Test of property: "+prop)
        
        
    def test_apod_characteristics(self):
        
        for page_type in TestApod.TEST_DATA.keys():
            self._test_harness(page_type, TestApod.TEST_DATA[page_type]) 
        
        
        
        
