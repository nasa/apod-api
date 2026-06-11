# coding= utf-8
import logging
import unittest
from unittest.mock import patch

import application

logging.basicConfig(level=logging.DEBUG)


@patch("application._abort")
class TestPageNotFound(unittest.TestCase):
    def test(self, mock_abort):
        GIVEN = Exception("example exception")
        application.page_not_found(GIVEN)
        mock_abort.assert_called_once()
