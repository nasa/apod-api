import unittest
import apod


class TestApod(unittest.TestCase):
    """Test the extraction of APOD characteristics."""
    def setUp(self):
        self.date = '2013-10-01'

    def test_apod_characteristics(self):
        explanation, title, url = apod._apod_characteristics(self.date)

        # Test returned Title
        expected_title = 'Filaments of the Vela Supernova Remnant'
        self.assertEqual(title, expected_title)
