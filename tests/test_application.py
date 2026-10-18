import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

import application


class TestApodEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        application.app.config["TESTING"] = True

    def test_home_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_invalid_field_abort(self):
        response = self.client.get("/v1/apod/?invalid_param=123")
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertIn("Bad Request: incorrect field passed.", json_data["msg"])

    def test_invalid_field_combination_abort(self):
        # Passing both count and date is an invalid combination
        response = self.client.get("/v1/apod/?date=2026-09-01&count=5")
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertIn("Bad Request: invalid field combination passed.", json_data["msg"])

    def test_invalid_count_range(self):
        response = self.client.get("/v1/apod/?count=30")
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertIn("cannot exceed 25", json_data["msg"])

    def test_start_date_after_end_date(self):
        response = self.client.get("/v1/apod/?start_date=2026-09-10&end_date=2026-09-01")
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertIn("start_date cannot be after end_date", json_data["msg"])

    @patch("application.requests.get")
    def test_get_json_for_date_mock(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "title": "Chasing the Moon's Shadow",
            "hdurl": "https://assets.science.nasa.gov/image.jpg",
            "date": "2026-09-05",
        }
        mock_get.return_value = mock_resp

        response = self.client.get("/v1/apod/?date=2026-09-05")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["title"], "Chasing the Moon's Shadow")
        self.assertEqual(data["url"], "https://assets.science.nasa.gov/image.jpg")
        self.assertEqual(data["service_version"], "v1")

    @patch("application.requests.get")
    def test_get_json_for_date_range_mock(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "title": "Day 1",
                "hdurl": "https://assets.science.nasa.gov/day1.jpg",
                "date": "2026-09-01",
            },
            {
                "title": "Day 2",
                "hdurl": "https://assets.science.nasa.gov/day2.jpg",
                "date": "2026-09-02",
            },
        ]
        mock_get.return_value = mock_resp

        response = self.client.get("/v1/apod/?start_date=2026-09-01&end_date=2026-09-02")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["url"], "https://assets.science.nasa.gov/day1.jpg")
        self.assertEqual(data[1]["url"], "https://assets.science.nasa.gov/day2.jpg")

    def test_page_not_found(self):
        response = self.client.get("/nonexistent-url")
        self.assertEqual(response.status_code, 404)
