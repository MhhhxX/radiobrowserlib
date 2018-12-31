import unittest
import re
import xml.etree.ElementTree as ET
from ..request import RadioBrowserRequest
from ..api import RadioApi, PlayRadioApi, SearchRadioApi
from ..apifacade import ApiFacade
from builtins import str


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.url = "http://www.radio-browser.info/webservice/{}/countries"
        self.radioRequest = RadioBrowserRequest('radiobrowserpy', '0.0.1')

    def test_request_json(self):
        response = self.radioRequest(self.url.format("json"), 'json', encoding=True)
        self.assertNotEqual(len(response), 0)
        self.assertIsInstance(response, list)

    def test_request_xml(self):
        response = self.radioRequest(self.url.format("xml"), 'xml', encoding=True)
        self.assertIsInstance(response, ET.Element)

    def test_request_plain(self):
        response = self.radioRequest(self.url.format("json"))
        self.assertNotEqual(len(response), 0)
        self.assertIsInstance(response, str)


class Api(unittest.TestCase):
    def setUp(self):
        self.radioapi = RadioApi('json', True, 'radiobrowserpy', '0.0.1')
        self.play_api = PlayRadioApi('json', True, 'radiobrowserpy', '0.0.1')
        self.search_api = SearchRadioApi('json', True, 'radiobrowserpy', '0.0.1')

    def test_set_output_format(self):
        value = 'xml'
        self.radioapi.output_format = value
        self.play_api.output_format = value
        self.search_api.output_format = value
        self.assertTrue(self.radioapi.api_url.endswith(value + '/'))
        self.assertTrue(self.play_api.api_url.endswith(value + '/'))
        self.assertTrue(re.match(r".+" + value + ".+", self.search_api.api_url) is not None)
        for value in ['m3u', 'pls']:
            self.play_api.output_format = value
            self.search_api.output_format = value
            self.assertTrue(self.play_api.api_url.endswith(value + '/'))
            self.assertTrue(re.match(r".+" + value + ".+", self.search_api.api_url) is not None)
        for value in ['ttl', 'xspf']:
            self.search_api.output_format = value
            self.assertTrue(re.match(r".+" + value + ".+", self.search_api.api_url) is not None)
        self.assertRaises(ValueError, self.radioapi._set_output_format, 'weifj')
        self.assertRaises(ValueError, self.play_api._set_output_format, 'efew')
        self.assertRaises(ValueError, self.search_api._set_output_format, 'weggw')


if __name__ == '__main__':
    unittest.main()
