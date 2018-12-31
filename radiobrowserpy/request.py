import requests
import xml.etree.ElementTree as ET
import json
from future.utils import PY3

HEADER = {'user-agent': 'radiokodilib/0.0.1'}


class RadioBrowserRequest:

    def __init__(self, app_name, app_version):
        self.header = {'user-agent': app_name + '/' + app_version}

    def __call__(self, url, outputformat='json', encoding=False, params=None):
        r = requests.get(url, params=params)
        if hasattr(self, '_to_' + outputformat) and encoding:
            func = getattr(self, '_to_' + outputformat)
            return func(r)
        return self._to_plain(r)

    def _to_json(self, request):
        return json.loads(request.text)

    def _to_xml(self, request):
        if PY3:
            return ET.fromstring(request.text)
        return ET.fromstring(request.text.encode('UTF-8'))

    def _to_plain(self, request):
        return request.text
