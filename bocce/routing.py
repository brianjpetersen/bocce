# standard libraries
import os
import re
import collections
import collections.abc
import inspect
import posixpath
import copy
# third party libraries
pass
# first party libraries
from . import (utils, )


__where__ = os.path.dirname(os.path.abspath(__file__))


class Route:
    
    _dsl_to_regex_pattern = re.compile(
        '{(?P<curly_segment>[^/]+?)}|<(?P<pointy_segment>[^/]+?)>'
    )
    
    def __init__(self, path, response, methods=('GET', None, ),
                 subdomains=('www', None, )):
        self._arg_path = path
        self._path = path.lstrip(' /').rstrip()
        self.response = response
        if isinstance(methods, str):
            raise TypeError(
                'The variable methods must be an iterable of string-likes.'
            )
        self.methods = set(methods)
        if isinstance(subdomains, str):
            raise TypeError(
                'The variable subdomains must be an iterable of string-likes.'
            )
        self.subdomains = set(subdomains)
        # counting matches
        self._number_curly_segments = 0
        self._number_pointy_segments = 0
        self._number_verbatim_segments = None
        # construct route regex
        self._regex = re.compile(
            re.sub(
                self._dsl_to_regex_pattern,
                self._sub_regex_for_dsl, 
                '\A{}\Z'.format(self.path)
            )
        )
    
    @property
    def path(self):
        return self._path
    
    def copy(self):
        return copy.deepcopy(self)
    
    @property
    def number_curly_segments(self):
        return self._number_curly_segments
    
    @property
    def number_pointy_segments(self):
        return self._number_pointy_segments
    
    @property
    def number_verbatim_segments(self):
        if self._number_verbatim_segments is None:
            number_segments = len(self.path.rstrip('/').split('/'))
            number_dsl_segments = self.number_pointy_segments + self.number_curly_segments
            self._number_verbatim_segments = number_segments - number_dsl_segments
        return self._number_verbatim_segments
    
    def match(self, path, method=None, subdomain=None):
        if method not in self.methods:
            return None
        if subdomain not in self.subdomains:
            return None
        match = self._regex.match(path.lstrip(' /').rstrip())
        if match is None:
            return None
        segments = match.groupdict()
        return segments
    
    def _sub_regex_for_dsl(self, match):
        match = match.groupdict()
        curly_segment = match['curly_segment']
        pointy_segment = match['pointy_segment']
        if curly_segment is not None:
            self._number_curly_segments += 1
            return '(?P<{}>[^/]*?)'.format(curly_segment)
        elif pointy_segment is not None:
            self._number_pointy_segments += 1
            return '(?P<{}>.*)'.format(pointy_segment)
        else:
            raise ValueError # should never happen
    
    def __str__(self):
        return '{} => {}'.format(self.path, self.response)
    
    def __repr__(self):
        return '{}{}'.format(
            self.__class__.__name__,
            (
                self._arg_path,
                self.response,
                tuple(self.methods),
                tuple(self.subdomains),
            )
        )


class Routes(collections.UserList):
    
    def __init__(self, cache_size=1e6):
        super(Routes, self).__init__()
        self.cache = utils.LRUCache(cache_size)
    
    def add_routes(self, path, routes):
        for route in routes:
            self.append(
                Route(
                    posixpath.join(path, route.path),
                    route.response,
                    route.methods,
                    route.subdomains,
                )
            )
    
    def add_response(self, path, response, methods=('GET', None, ), 
                     subdomains=('www', None, )):
        route = Route(path, response, methods, subdomains)
        self.append(route)
    
    def match(self, path, method=None, subdomain=None):
        key = (path, method, subdomain)
        if key in self.cache:
            return self.cache[key]
        matches = []
        for index, route in enumerate(self):
            segments = route.match(path, method, subdomain)
            if segments is None:
                continue
            priority = -index
            match = (
                route.number_verbatim_segments,
                route.number_curly_segments,
                priority,
                route,
                segments,
            )
            matches.append(match)
        if len(matches) > 0:
            best_match = max(matches)
            _, _, _, route, segments = best_match
            self.cache[key] = route, segments
            return route, segments
        else:
            return None
