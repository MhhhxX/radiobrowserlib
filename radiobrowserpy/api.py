import sys
import functools

from .request import *
from .constants import *
from builtins import super

if sys.version_info[0:2] >= (3, 4):  # Python v3.4+?
    wraps = functools.wraps  # built-in has __wrapped__ attribute
else:
    def wraps(wrapped, assigned=functools.WRAPPER_ASSIGNMENTS,
              updated=functools.WRAPPER_UPDATES):
        def wrapper(f):
            f = functools.wraps(wrapped, assigned, updated)(f)
            f.__wrapped__ = wrapped  # set attribute missing in earlier versions
            return f

        return wrapper


class RequestDecorator:
    def __init__(self, endpoint, nested=False):
        self.endpoint = endpoint
        self.nested = nested

    def __call__(self, f):
        @wraps(f)
        def make_request(innerself, *args, **kwargs):
            url, selector, params = f(innerself, *args, **kwargs)
            if isinstance(selector, list):
                filter_endpoint = self.endpoint.format(*selector)
            else:
                filter_endpoint = self.endpoint.format(selector)
            url += filter_endpoint
            if self.nested:
                return url, selector, params
            return innerself.radiorequest(url, outputformat=innerself.output_format, encoding=innerself.encoding,
                                          params=params)

        return make_request


class Format(object):
    formats = ['json', 'xml']

    def __init__(self, output_format, encoding, app_name, app_version):
        """
        Inits Api class

        :param str output_format: response format of the webservice
        :param bool encoding: if True, the Api encodes the response in the given output format if supported
        """
        self.encoding = encoding
        self.radiorequest = RadioBrowserRequest(app_name, app_version)
        self.output_format = output_format

    def __call__(self, encoding, params, endpoint, outputformat=None):
        """
        Sends a arbitrary request to the given endpoint at the webservice.

        :param str endpoint: an endpoint at the webservice
        :param dict params: parameters which can be sent with the request
        :param bool encoding: if True and output format support, the response becomes encoded in a python object in the
               given output format
        :param str outputformat: format of the webservice response
        :return: response of the webservice as str or encoded as output format if encoding=True
        """
        if outputformat is None:
            url = BASEURL + self.output_format + '/' + endpoint
            return self.radiorequest(url, outputformat=self.output_format, encoding=self.encoding, params=params)
        url = BASEURL + outputformat + '/' + endpoint
        return self.radiorequest(url, outputformat=outputformat, encoding=self.encoding, params=params)

    def _get_output_format(self):
        return self._output_format

    def _set_output_format(self, value):
        if value not in self.formats:
            msg = 'format "%s" not supported! Supported Formats: %s\n' % (value, str(self.formats))
            raise ValueError(msg)
        self._output_format = value
        self._update_api_url()

    def _get_encoding(self):
        return self._encoding

    def _set_encoding(self, value):
        self._encoding = value

    def _update_api_url(self):
        raise NotImplementedError()

    output_format = property(_get_output_format, _set_output_format)
    encoding = property(_get_encoding, _set_encoding)


class PlayFormat(Format):
    def _update_api_url(self):
        raise NotImplementedError()

    formats = ['json', 'xml', 'm3u', 'pls']

    def __init__(self, output_format, encoding, app_name, app_version):
        super().__init__(output_format, encoding, app_name, app_version)


class SearchFormat(PlayFormat):
    def _update_api_url(self):
        raise NotImplementedError()

    formats = ['json', 'xml', 'm3u', 'pls', 'xspf', 'ttl']

    def __init__(self, output_format, encoding, app_name, app_version):
        super().__init__(output_format, encoding, app_name, app_version)


class RadioApi(Format):
    def _update_api_url(self):
        self.api_url = BASEURL + self.output_format + '/'

    base_doc = '\n\tReturns a list of all {} in the database.\n\n' \
               '\t:param str selector: if set only the function only return the ones containing the selector as substring\n' \
               '\t:param order str in ["value", "stationcount"]: name of the attribute the result list will be sorted by\n' \
               '\t:param reverse bool: if set to True, the response list gets inverted\n' \
               '\t:param hidebroken bool: if set to True, the response does not contain any broken radio stations\n' \
               '\t:return: list of all {} in the database\n' \
               ''

    def __init__(self, output_format, encoding, app_name, app_version):
        self.api_url = BASEURL + output_format + '/'
        super().__init__(output_format, encoding, app_name, app_version)

    @RequestDecorator('countries/{}')
    def countries(self, selector='', order='value', reverse=False, hidebroken=False):
        return self.api_url, selector, {'order': order, 'reverse': reverse, 'hidebroken': hidebroken}

    @RequestDecorator('codecs/{}')
    def codecs(self, selector='', order='value', reverse=False, hidebroken=False):
        return self.api_url, selector, {'order': order, 'reverse': reverse, 'hidebroken': hidebroken}

    @RequestDecorator('states/{}')
    def states(self, selector='', order='value', reverse=False, hidebroken=False, country=None):
        """
        Returns a list of all states in the database.

        :param str selector: if set only the function only return the ones containing the selector as substring
        :param str in ["value", "stationcount"] order: name of the attribute the result list will be sorted by
        :param bool reverse: rerverses the result list if set to true
        :param bool hidebroken: do not count broken stations
        :param str country: filter states by country name
        :return: list of all states in the database
        """
        return self.api_url, selector, {'order': order, 'reverse': reverse, 'hidebroken': hidebroken,
                                        'country': country}

    @RequestDecorator('languages/{}')
    def languages(self, selector='', order='value', reverse=False, hidebroken=False):
        return self.api_url, selector, {'order': order, 'reverse': reverse, 'hidebroken': hidebroken}

    @RequestDecorator('tags/{}')
    def tags(self, selector='', order='value', reverse=False, hidebroken=False):
        return self.api_url, self.countries.__wrapped__(selector, order, reverse, hidebroken)

    @RequestDecorator('stations/')
    def stations(self, order='name', reverse=False, offset=0, limit=1000000):
        """
        Returns a list of stations in the database.
        :param str in ["value", "stationcount"] order: name of the attribute the result list will be sorted by
        :param bool reverse: rerverses the result list if set to true
        :param int offset: starting value of the result list from the database, for example if you want to do paging on
        the serverside
        :param limit: number of returned data rows (stations) starting with offset
        :return: stations in the database according to given parameters
        """
        return self.api_url, [], {'order': order, 'reverse': reverse, 'offset': offset, 'limit': limit}

    @RequestDecorator('checks/')
    def checks(self, seconds=0, stationuuid=None):
        """
        Returns a list of station check results.
        :param int seconds: if > 0 then it will only return history entries from the last 'seconds' seconds
        :param str stationuuid: If set, list only checks for the matching station.
        :return: a station list of check results.
        """
        return self.api_url, [], {'seconds': seconds, 'stationuuid': stationuuid}

    @RequestDecorator('stations/deleted/{}')
    def deleted_stations(self, stationid=''):
        """
        Returns a list of stations that got deleted in the last 30 days.
        :param str stationid: If set, deleted station with this id gets returned
        :return: list of deleted stations
        """
        return self.api_url, stationid, None

    @RequestDecorator('stations/changed/{}')
    def changed_stations(self, stationid='', seconds=0):
        """
        Returns a list of old versions of stations from the last 30 days.

        :param int seconds: if > 0 then it will only return history entries from the last 'seconds' seconds
        :param str stationid: If set, history of station with this id gets returned.
        :return: a station list of old version of stations.
        """
        return self.api_url, stationid, {'seconds': seconds}

    @RequestDecorator('vote/{}')
    def vote_for_station(self, stationid):
        """
        Increase the vote count for the station by one. Can only be done by the same ip adress for one station every 10
        minutes.
        :param stationid: id of the station
        :return: Returns the changed station as result if it worked.
        """
        return self.api_url, stationid, None

    @RequestDecorator('delete/{}')
    def delete_station(self, stationid):
        """
        The station will be deleted from the public list and moved to a deleted list. It will stay there for 30 days and
        then removed from the system. As long as it is in the deleted list it can be @self.undeleted at any time.
        :param stationid: id of the station
        :return: Returns the status of this action.
        """
        return self.api_url, stationid, None

    @RequestDecorator('undelete/{}')
    def undelete_station(self, stationid):
        """
        Undeletes a station which was deleted in the last 30 days.

        :param stationid: id of the station
        :return: Returns the status of this action.
        """
        return self.api_url, stationid, None

    @RequestDecorator('revert/{}/{}')
    def revert_station(self, stationid, changeid):
        """
        Reverts a change to a station that was done in the last 30 days.

        :param stationid: id of the station
        :param changeid: id of a old version of a station
        :return: Returns the status of this action.
        """
        return self.api_url, [stationid, changeid], None

    @RequestDecorator('add/')
    def add_station(self, name, url, homepage=None, favicon=None, country=None, state=None, language=None, tags=None):
        """
        Add a radio station to the database.

        :param name: the name of the radio station. Max 400 chars.
        :param url: the url of the station
        :param homepage: the homepage url of the station
        :param favicon: the url of an image file (jpg or png)
        :param country: The name of the country where the radio station is located
        :param state: The name of the part of the country where the station is located
        :param language: The main language which is used in spoken text parts of the radio station.
        :param tags: A list of tags separated by commas, which describe the station.
        :return: Returns the status of this action.
        """
        return self.api_url, [], \
               {
                   'name': name,
                   'url': url,
                   'homepage': homepage,
                   'favicon': favicon,
                   'country': country,
                   'state': state,
                   'language': language,
                   'tags': tags
               }

    @RequestDecorator('edit/{}')
    def edit_station(self, stationid, name, url, homepage=None, favicon=None, country=None, state=None, language=None,
                     tags=None):
        """
        Edit a radio station. You can only change some of the values, even only one value, by sending just the parameter
        you want to change. The rest of the information of the edited station will stay the same. The Station is not
        saved, if the given url is not working

        :param stationid: id of the station to edit
        :param name: the name of the radio station. Max 400 chars.
        :param url: the url of the station
        :param homepage: the homepage url of the station
        :param favicon: the url of an image file (jpg or png)
        :param country: The name of the country where the radio station is located
        :param state: The name of the part of the country where the station is located
        :param language: The main language which is used in spoken text parts of the radio station.
        :param tags: A list of tags separated by commas, which describe the station.
        :return: Returns the status of this action.
        """
        return self.api_url, stationid, \
               {
                   'name': name,
                   'url': url,
                   'homepage': homepage,
                   'favicon': favicon,
                   'country': country,
                   'state': state,
                   'language': language,
                   'tags': tags
               }

    @RequestDecorator('stats')
    def server_stats(self):
        """
        Webservice stats

        :return: stats of the Webservice
        """
        return self.api_url, [], None

    list_funcs = [countries, codecs, languages, tags]
    for func in list_funcs:
        func.__doc__ = base_doc.format(func.__name__, func.__name__)


class PlayRadioApi(PlayFormat):

    def __init__(self, output_format, encoding, app_name, app_version):
        self.api_url = BASEURL + 'v2/' + output_format + '/'
        super().__init__(output_format, encoding, app_name, app_version)

    def _update_api_url(self):
        self.api_url = BASEURL + 'v2/' + self.output_format + '/'

    @RequestDecorator('url/{}')
    def playable_url(self, stationid):
        """
        Returns the playable url for the station. Any Playlist (PLS, ASX, M3U) decoding will be done for you. This API
        call will count as a click on the station.

        :param stationid: id of the station
        :return: playable url, status message
        """
        return self.api_url, stationid, None


class SearchRadioApi(SearchFormat):
    base_doc = '\n\tWill get a list of radio stations that match the search. The variants with "exact" will only search ' \
               '\n' \
               '\tfor perfect matches. The others will match if the station attribute contains the searchterm. Please ' \
               '\n' \
               '\tuse Playable station url API call to get the real station url and also let the click be counted.\n\n' \
               '' \
               '\t:param str searchterm: search term\n' \
               '\t:param str order in ["name", "url", "homepage", "favicon", "tags", "country", "state", "language", \n' \
               '\t\t"votes", "negativeotes", "codec", "bitrate", "lastcheckok", "lastchecktime", "clicktimestamp", \n' \
               '\t\t"clickcount", "clicktrend"]: \n\t\tname of the attribute the result list will be sorted by\n' \
               '\t:param bool reverse: rerverses the result list if set to true\n' \
               '\t:param int offset: starting value of the result list from the database, for example if you want to \n' \
               '\tdo paging on the serverside\n' \
               '\t:param int limit: number of returned datarows (stations) starting with offset\n' \
               '\t:return list of search results from the webservice\n'

    def __init__(self, output_format, encoding, app_name, app_version):
        self.api_url = BASEURL + output_format + '/stations/'
        super().__init__(output_format, encoding, app_name, app_version)

    def _update_api_url(self):
        self.api_url = BASEURL + self.output_format + '/stations/'

    @RequestDecorator('byid/{}')
    def stations_byid(self, searchterm, order='value', reverse='false', offset=0, limit=1000000):
        return self.api_url, searchterm, {'order': order, 'reverse': reverse, 'offset': offset, 'limit': limit}

    @RequestDecorator('byuuid/{}')
    def stations_byuuid(self, searchterm, order='value', reverse='false', offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('byname/{}')
    def stations_byname(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bynameexact/{}')
    def stations_bynameexact(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bycodec/{}')
    def stations_bycodec(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bycodecexact/{}')
    def stations_bycodecexact(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bycountry/{}')
    def stations_bycountry(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bycountryexact/{}')
    def stations_bycountry(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bystate/{}')
    def stations_bystate(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bystateexact/{}')
    def stations_bystateexact(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bylanguage/{}')
    def stations_bylanguage(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bylanguageexact/{}')
    def stations_bylanguageexact(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bytag/{}')
    def stations_bytag(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('bytagexact/{}')
    def stations_bytagexact(self, searchterm, order='name', reverse=False, offset=0, limit=1000000):
        return self.stations_byid.__wrapped__(self, searchterm, order, reverse, offset, limit)

    @RequestDecorator('byurl')
    def stations_byurl(self, url):
        """
        Will get a list of radio stations that have an exact url match, supported
        output formats: JSON, XML, M3U, PLS, XSPF, TTL

        :param url: url of the station
        :return: a list of radio stations matching url
        """
        return self.api_url, [], {'url': url}

    @RequestDecorator('topclick/{}')
    def top_click(self, rowcount=''):
        """
        Returns a list of the stations that are clicked the most. You can add a parameter with the number of wanted
        stations, supported output formats: JSON, XML, M3U, PLS, XSPF, TTL

        :param rowcount: specifies number of wanted results, e.g top 5 clicked stations
        :return: list of stations that are clicked the most
        """
        return self.api_url, rowcount, None

    @RequestDecorator('topvote/{}')
    def top_vote(self, rowcount=''):
        """
        Returns a list of the highest voted stations. You can add a parameter with the number of wanted stations.

        :param rowcount: specifies number of wanted results, e.g top 5 voted stations
        :return: list of highest voted stations
        """
        return self.api_url, rowcount, None

    @RequestDecorator('lastclick/{}')
    def last_click(self, rowcount=''):
        """
        Returns a list of stations that got clicked recently.

        :param rowcount: specifies number of wanted results, e.g top 5 last clicked stations
        :return: list of recently clicked stations
        """
        return self.api_url, [rowcount], None

    @RequestDecorator('lastchange/{}')
    def last_change(self, rowcount=''):
        """
        Returns a list of stations that got added or changed recently.

        :param rowcount: specifies number of wanted results, e.g top 5 last changed stations
        :return: list of last changed stations
        """
        return self.api_url, rowcount, None

    @RequestDecorator('improvable/{}')
    def improvable_stations(self, rowcount=''):
        """
        Returns a list of the stations that need improvement, which means they do not have e.g.: tags, country,
        state,.. information.

        :param rowcount: specifies number of wanted results, e.g top 5 improvable stations
        :return: list of improvable stations
        """
        return self.api_url, rowcount, None

    @RequestDecorator('broken/{}')
    def broken_stations(self, rowcount=''):
        """
        Returns a list of the stations that did not pass the connection test.

        :param rowcount: specifies number of wanted results, e.g top 5 broken stations
        :return: list of broken stations
        """
        return self.api_url, rowcount, None

    @RequestDecorator('search/')
    def search(self, name=None, name_exact='false', country=None, country_exact='false', state=None,
               state_exact='false',
               language=None, language_exact='false', tag=None, tag_exact='false', tag_list=None, bitrate_min=0,
               bitrate_max=1000000, order='name', reverse='false', offset=0, limit=100000):
        """
        Will get a list of radio stations that match the search. It will match if the station attribute contains the
        searchterm. Please use Playable station url API call to get the real station url and also let the click be
        counted.

        :param name: name of the station
        :param name_exact: True: only exact matches, otherwise all matches.
        :param country: country of the station
        :param country_exact: True: only exact matches, otherwise all matches.
        :param state: state of the station
        :param state_exact: True: only exact matches, otherwise all matches.
        :param language: language of the station
        :param language_exact: True: only exact matches, otherwise all matches.
        :param tag: a tag of the station
        :param tag_exact: True: only exact matches, otherwise all matches.
        :param tag_list: a comma separated list of tag. It can also be an array of string in json HTTP POST parameters.
            All tags in list have to match.
        :param bitrate_min: minimum of kbps for Bitrate field of stations in result
        :param bitrate_max: maximum of kbps for Bitrate field of stations in result
        :param order: name of the attribute the result list will be sorted by
        :param reverse: rerverses the result list if set to true
        :param offset: starting value of the result list from the database, for example if you want to do paging on the
            serverside
        :param limit: number of returned datarows (stations) starting with offset
        :return: list of search results
        """
        return self.api_url, \
               '', \
               {
                   'name': name,
                   'nameExact': name_exact,
                   'country': country,
                   'countryExact': country_exact,
                   'state': state,
                   'stateExact': state_exact,
                   'language': language,
                   'languageExact': language_exact,
                   'tag': tag,
                   'tagExact': tag_exact,
                   'tagList': tag_list,
                   'bitrateMin': bitrate_min,
                   'bitrateMax': bitrate_max,
                   'order': order,
                   'reverse': reverse,
                   'offset': offset,
                   'limit': limit
               }

    __search_funcs = [stations_byid, stations_byuuid, stations_bycodec, stations_bycodecexact, stations_bycountry,
                      stations_bylanguage, stations_bylanguageexact, stations_byname, stations_bynameexact,
                      stations_bystate, stations_bystateexact, stations_bytag, stations_bytagexact]
    for func in __search_funcs:
        func.__doc__ = base_doc
