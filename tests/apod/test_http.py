# coding= utf-8
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import requests

from apod import utility


def _mock_response(status_code=200, content=b"", apparent_encoding="utf-8"):
    res = MagicMock(spec=requests.Response)
    res.status_code = status_code
    res.content = content
    res.text = content.decode("utf-8", errors="replace")
    res.apparent_encoding = apparent_encoding
    if status_code >= 400:
        res.raise_for_status.side_effect = requests.HTTPError(
            "%s Error" % status_code, response=res
        )
    else:
        res.raise_for_status.return_value = None
    return res


class TestOutboundRequests(unittest.TestCase):
    """Offline tests for timeout/retry hardening of requests made to the
    backing APOD service. Regression tests for connection timeout issues
    (issue #163)."""

    def test_apod_page_request_uses_timeout(self):
        """The request for the APOD page must carry an explicit timeout so a
        hung upstream connection cannot hold a worker indefinitely."""
        with patch.object(utility, "session") as mock_session:
            mock_session.get.return_value = _mock_response(status_code=404)
            result = utility._get_apod_chars(datetime(2020, 1, 1), thumbs=False)

        self.assertIsNone(result)
        _, kwargs = mock_session.get.call_args
        self.assertEqual(kwargs.get("timeout"), utility.REQUEST_TIMEOUT)

    def test_missing_page_returns_none(self):
        """A 404 from the backing service must still map to None (which the
        application layer turns into a 404 response)."""
        with patch.object(utility, "session") as mock_session:
            mock_session.get.return_value = _mock_response(status_code=404)
            self.assertIsNone(
                utility._get_apod_chars(datetime(2020, 1, 1), thumbs=False)
            )

    def test_persistent_upstream_error_raises(self):
        """A 5xx that survives the retries must raise instead of handing an
        upstream error page to the parser."""
        with patch.object(utility, "session") as mock_session:
            mock_session.get.return_value = _mock_response(status_code=503)
            with self.assertRaises(requests.HTTPError):
                utility._get_apod_chars(datetime(2020, 1, 1), thumbs=False)

    def test_session_is_configured_to_retry_transient_failures(self):
        """The shared session must retry transient upstream failures with
        backoff before giving up."""
        adapter = utility.session.get_adapter(utility.BASE)
        retries = adapter.max_retries

        self.assertGreaterEqual(retries.total, 1)
        self.assertGreater(retries.backoff_factor, 0)
        for status in (500, 502, 503, 504):
            self.assertIn(status, retries.status_forcelist)
        self.assertIn("GET", retries.allowed_methods)
        # raise_on_status=False is load-bearing: it makes the session hand the
        # final 5xx response back so raise_for_status() in _get_apod_chars is
        # what surfaces the error (instead of urllib3 raising RetryError).
        self.assertFalse(retries.raise_on_status)
        # Retry-After must be ignored: a server-specified delay on a 429/503
        # would otherwise sleep the worker past gunicorn's timeout.
        self.assertFalse(retries.respect_retry_after_header)

    def test_hung_connection_budget_fits_worker_timeout(self):
        """Worst-case wall-clock for hung upstream connections must stay
        below gunicorn's default 30s worker timeout, otherwise the worker is
        killed mid-retry and the client sees a dropped connection."""
        retries = utility.session.get_adapter(utility.BASE).max_retries

        def backoff_sleeps(num_retries):
            # urllib3 2.x sleeps 0 before the first retry, then
            # backoff_factor * 2^(n-1) before retry n
            return sum(
                retries.backoff_factor * (2**n) for n in range(1, num_retries)
            )

        connect_attempts = min(retries.connect, retries.total) + 1
        worst_connect_hang = (
            connect_attempts * utility.CONNECT_TIMEOUT
            + backoff_sleeps(connect_attempts - 1)
        )
        self.assertLess(worst_connect_hang, 30)

        read_attempts = min(retries.read, retries.total) + 1
        worst_read_hang = read_attempts * (
            utility.CONNECT_TIMEOUT + utility.READ_TIMEOUT
        ) + backoff_sleeps(read_attempts - 1)
        self.assertLess(worst_read_hang, 30)

    def test_vimeo_thumbnail_request_uses_timeout(self):
        """The Vimeo thumbnail lookup must also carry an explicit timeout."""
        vimeo_response = _mock_response()
        vimeo_response.json.return_value = [
            {"thumbnail_large": "https://i.vimeocdn.com/video/foo_640.jpg"}
        ]
        with patch.object(utility, "session") as mock_session:
            mock_session.get.return_value = vimeo_response
            thumb = utility._get_thumbs("https://player.vimeo.com/video/12345")

        self.assertEqual(thumb, "https://i.vimeocdn.com/video/foo_640.jpg")
        _, kwargs = mock_session.get.call_args
        self.assertEqual(kwargs.get("timeout"), utility.REQUEST_TIMEOUT)

    def test_vimeo_thumbnail_upstream_error_raises(self):
        """A persistent upstream error from the Vimeo API must surface as a
        clear HTTPError instead of a JSON parsing failure on an error page."""
        with patch.object(utility, "session") as mock_session:
            mock_session.get.return_value = _mock_response(status_code=503)
            with self.assertRaises(requests.HTTPError):
                utility._get_thumbs("https://player.vimeo.com/video/12345")
