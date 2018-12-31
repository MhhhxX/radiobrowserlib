from .api import RadioApi, PlayRadioApi, SearchRadioApi


class ApiFacade:
    def __init__(self, output_format='json', playable_format='json',
                 search_format='json', encoding=False, appname='radiobrowserpy', appversion='0.0.1'):
        """
        Creates a new ApiFacade instance for making requests to Radio-browser.info webservice. The responses are json
        strings by default.

        When setting the "format" parameters, please consider the following:

        Following api methods support the given output_format:
        the given format: ['add_station', 'changed_stations', 'checks', 'codecs', 'countries', 'delete_station',
        'deleted_stations', 'edit_station', 'func', 'languages', 'revert_station', 'server_stats',
        'states', 'stations', 'tags', 'undelete_station', 'vote_for_station']

        'playable_url' method supports the given playable_format

        Following api methods support the given search_format: ['broken_stations', 'func', 'improvable_stations',
        'last_change', 'last_click', 'search', 'stations_bycodec', 'stations_bycodecexact',
        'stations_bycountry', 'stations_byid', 'stations_bylanguage', 'stations_bylanguageexact', 'stations_byname',
        'stations_bynameexact', 'stations_bystate', 'stations_bystateexact', 'stations_bytag', 'stations_bytagexact',
        'stations_byurl', 'stations_byuuid', 'top_click', 'top_vote']

        :param output_format in ['json', 'xml']: output format for basic api requests.
        :param playable_format in ['json', 'xml', 'm3u', 'pls']: output format for api requests which return play
        related. Supported by method 'playable_url'
        api responses
        :param search_format in ['json', 'xml', 'm3u', 'pls', 'ttl', 'xspf']: output format for search requests.
        :param encoding: if True and output format is supported, the returned api response becomes encoded
            in related python objects
        :param appname name of your application (will be send in the header of each http request).
        :param appversion version of your application (will be send in the header of each http request)

        Example:
            from radiobrowserlib import ApiFacade
            facade = ApiFacade()
            facade.countries() -> returns a list of available countries in the database as a string

            # arbitrary request
            facade(encoding=True, params=None, endpoint='countries', output_format='json') -> returns a list of all
                countries as a python list

        """
        self._radio_api = RadioApi(output_format, encoding, appname, appversion)
        self._play_api = PlayRadioApi(playable_format, encoding, appname, appversion)
        self._search_api = SearchRadioApi(search_format, encoding, appname, appversion)
        self.__api_list = [self._radio_api, self._play_api, self._search_api]
        self.__all_api_funcs = []
        self.__init_api_funcs()

    def __getattr__(self, item):
        for api in self.__api_list:
            if hasattr(api, item):
                return getattr(api, item)
        alternatives = self.__search_func(item)
        msg = 'RadioApi has no attribute "%s". Maybe you mean:\n' % item
        for alt in alternatives:
            msg += '\t' + alt + '\n'
        raise AttributeError(msg[:-1])

    def set_output_format(self, value):
        """
        Sets the output format for basic api requests

        :param value: new output format. Possible values: ['json', 'xml']
        """
        self._radio_api.output_format = value

    def set_playable_format(self, value):
        """
        Sets the output format for play related api requests

        :param value: new output format. Possible values: ['json', 'xml', 'm3u', 'pls']
        """
        self._play_api.output_format = value

    def set_search_format(self, value):
        """
        Sets the output format for search related api requests

        :param value: new output format. Possible values: ['json', 'xml', 'm3u', 'pls', 'ttl', 'xspf']
        """
        self._search_api.output_format = value

    def help(self, name=None):
        """
        Prints either the documentation of the function with a given name of if no name was given it prints the doc
        strings of all available api functions

        :param name: name of a api function
        """
        if name is not None:
            help(getattr(self, name))
            return
        for func in self.__all_api_funcs:
            print(func.__name__)
            print(func.__doc__ + '\n\n')

    def __init_api_funcs(self):
        del self.__all_api_funcs[:]
        for api in self.__api_list:
            self.__all_api_funcs.extend([getattr(api, func) for func in dir(api)
                                         if callable(getattr(api, func)) and not func.startswith("_")])

    def __search_func(self, value):
        if len(value) == 1:
            return [func.__name__ for func in self.__all_api_funcs if func.__name__.startswith(value)]
        return [func.__name__ for func in self.__all_api_funcs if func.__name__.find(value) != -1]


if __name__ == '__main__':
    facade = ApiFacade()
