#!/bin/sh/python
# coding= utf-8
import unittest
from mock import patch
from apod import application
import logging

logging.basicConfig(level=logging.DEBUG)


@patch('application._abort')
class TestPageNotFound(unittest.TestCase):
    def test(self, mock_abort):
        GIVEN = Exception('example exception')
        applicaiton.page_not_found(GIVEN)
        mock_abort.assert_called_once()
