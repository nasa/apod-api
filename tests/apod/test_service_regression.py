#!/bin/sh/python
# coding= utf-8
"""Regression tests for the apod endpoint (mocked upstream, no network)."""
import unittest
from datetime import date as real_date
from unittest.mock import patch

from application import app


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


def apod_entry(d):
    return {
        "date": d,
        "title": f"APOD {d}",
        "hdurl": f"https://apod.nasa.gov/img/{d}.jpg",
        "url": f"https://science.nasa.gov/image-article/apod-{d}/",
        "media_type": "image",
        "explanation": "explanation text",
    }


class TestRegression(unittest.TestCase):
    """Issue #175 + silent 404 drop + 500 on unknown dates."""

    def setUp(self):
        self.client = app.test_client()

    def test_random_count_honored_despite_404(self):
        # count=3 must return 3 entries even when the upstream 404s some dates
        responses = [FakeResponse(404, {})] + [
            FakeResponse(200, apod_entry(f"2020-01-0{i}")) for i in range(1, 6)
        ]
        with patch("application.requests.get", side_effect=responses) as m:
            r = self.client.get("/v1/apod/?count=3")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 3)
        self.assertEqual(m.call_count, 4)  # 1 miss + 3 hits

    def test_start_date_defaults_end_to_today(self):
        # docstring contract: end_date defaults to the current date, not start+25
        today_yymmdd = real_date.today().strftime("%y%m%d")
        with patch(
            "application.requests.get",
            return_value=FakeResponse(200, [apod_entry("2026-08-02")]),
        ) as m:
            r = self.client.get("/v1/apod/?start_date=2026-08-01")
        self.assertEqual(r.status_code, 200)
        url = m.call_args.args[0]
        self.assertIn("date_from=260801", url)
        self.assertIn(f"date_to={today_yymmdd}", url)

    def test_range_stops_when_upstream_ignores_pagination(self):
        # upstream repeats page 1 -> stop instead of duplicating items
        page = [apod_entry(f"2026-08-{d:02d}") for d in range(1, 26)]
        with patch(
            "application.requests.get",
            side_effect=lambda url, **kw: FakeResponse(200, page),
        ) as m:
            r = self.client.get("/v1/apod/?start_date=2026-08-01&end_date=2026-09-14")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 25)
        self.assertEqual(m.call_count, 2)

    def test_range_follows_pagination(self):
        # upstream supports 'page' -> collect every page until empty
        p1 = [apod_entry(f"2026-09-{d:02d}") for d in range(1, 26)]
        p2 = [apod_entry(f"2026-08-{d:02d}") for d in range(1, 26)]
        p3 = [apod_entry(f"2026-07-{d:02d}") for d in range(1, 11)]
        with patch(
            "application.requests.get",
            side_effect=[
                FakeResponse(200, p1),
                FakeResponse(200, p2),
                FakeResponse(200, p3),
                FakeResponse(200, []),
            ],
        ):
            r = self.client.get("/v1/apod/?start_date=2026-07-01&end_date=2026-09-14")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 60)

    def test_unknown_date_returns_400_not_500(self):
        with patch(
            "application.requests.get",
            return_value=FakeResponse(404, {"code": "rest_no_route"}),
        ):
            r = self.client.get("/v1/apod/?date=banana")
        self.assertEqual(r.status_code, 400)
        self.assertIn("banana", r.get_json()["msg"])

    def test_valid_date_passthrough(self):
        # documented contract: 'url' matches the permalink, upstream native field
        entry = apod_entry("2026-09-08")
        with patch("application.requests.get", return_value=FakeResponse(200, entry)):
            r = self.client.get("/v1/apod/?date=2026-09-08")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["url"], entry["url"])
        self.assertEqual(body["hdurl"], entry["hdurl"])
        self.assertEqual(body["service_version"], "v1")

    def test_video_entry_without_hdurl(self):
        # hdurl is only "available" for some entries: must not crash the service
        entry = apod_entry("2026-09-13")
        del entry["hdurl"]
        entry["media_type"] = "video"
        with patch("application.requests.get", return_value=FakeResponse(200, entry)):
            r = self.client.get("/v1/apod/?date=2026-09-13")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["url"], entry["url"])
        self.assertEqual(body["media_type"], "video")

    def test_range_items_keep_permalink(self):
        page = [apod_entry(f"2026-08-{d:02d}") for d in range(1, 26)]
        with patch(
            "application.requests.get",
            side_effect=lambda url, **kw: FakeResponse(200, page),
        ):
            r = self.client.get("/v1/apod/?start_date=2026-08-01&end_date=2026-08-05")
        self.assertEqual(r.status_code, 200)
        for item in r.get_json():
            self.assertTrue(item["url"].startswith("https://science.nasa.gov/image-article/"))
            self.assertTrue(item["hdurl"].startswith("https://apod.nasa.gov/img/"))


if __name__ == "__main__":
    unittest.main()
