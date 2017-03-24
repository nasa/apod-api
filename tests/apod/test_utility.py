
import unittest
from apod import utility 
import logging

logging.basicConfig(level=logging.DEBUG)

class TestApod(unittest.TestCase):
    
    """Test the extraction of APOD characteristics."""
    def setUp(self):
        from datetime import datetime
        self.date = datetime (2013, 6, 13)  

    def test_apod_characteristics(self):
        #explanation, title, url 
        values = utility.parse_apod(self.date)

        # Test returned Explanation 
        expected_explan = 'You can see four planets in this serene'
        self.assertTrue(values[0].startswith(expected_explan))
        
        # Test returned Title
        expected_title = 'Four Planet Sunset'
        self.assertEqual(values[1], expected_title)
        
        # Test returned url
        expected_url = None
        self.assertEqual(values[2], expected_url)
        
        # Test returned copyright
        
        
