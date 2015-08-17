# standard libraries
import os
import heapq
import collections
# third party libraries
pass
# first party libraries
from . import (paths, caching, )


__all__ = ('Routes', 'Match', 'Mismatch', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class Match(object):

    def __init__(self, path, resource, priority, segments):
        self._path = path
        self._resource = resource
        self._priority = priority
        #
        self._segments = {}
        self._number_curly_segments = 0
        self._number_pointy_segments = 0
        self._number_verbatim_segments = 0
        for matched_segment, target_segment in segments:
            if isinstance(matched_segment, paths.CurlySegment):
                alias = matched_segment.alias
                target = target_segment.value
                self._segments[alias] = target
                self._number_curly_segments += 1
            elif isinstance(matched_segment, paths.PointySegment):
                alias = matched_segment.alias
                target = target_segment.value
                self._number_pointy_segments += 1
                if alias in self._segments:
                    self._segments[alias].append(target)
                else:
                    self._segments[alias] = [target, ]
            elif isinstance(matched_segment, paths.VerbatimSegment):
                self._number_verbatim_segments += 1
            else:
                raise TypeError()

    @property
    def number_curly_segments(self):
        return self._number_curly_segments

    @property
    def number_verbatim_segments(self):
        return self._number_verbatim_segments

    @property
    def number_pointy_segments(self):
        return self._number_pointy_segments

    @property
    def path(self):
        return self._path

    @property
    def resource(self):
        return self._resource

    @property
    def segments(self):
        return self._segments

    @property
    def priority(self):
        return self._priority

    @property
    def _comparison_tuple(self):
        return (self.number_verbatim_segments, self.number_curly_segments,
                self.priority)

    def __eq__(self, other):
        return self._comparison_tuple == other._comparison_tuple

    def __lt__(self, other):
        return self._comparison_tuple < other._comparison_tuple

    def __le__(self, other):
        return self._comparison_tuple <= other._comparison_tuple

    def __gt__(self, other):
        return self._comparison_tuple > other._comparison_tuple

    def __ge__(self, other):
        return self._comparison_tuple >= other._comparison_tuple


class Mismatch(Match):

    def __init__(self):
        self._path = None
        self._resource = None
        self._priority = -1
        #
        self._segments = {}
        self._number_curly_segments = 0
        self._number_pointy_segments = 0
        self._number_verbatim_segments = 0


mismatch = Mismatch()


def copy_list(a):
    """ Copy a list.  Could do this inline, but Alex Martelli claims 
        it is 'a weird syntax and it does not make sense to use it ever.'

    """
    return a[:]


class PotentialMatch(object):

    def __init__(self, path, parent, children, depth=0, matched_segments=None):
        self.parent = parent
        self.children = children
        self.path = path
        self.depth = depth
        if matched_segments is None:
            matched_segments = []
        self.matched_segments = matched_segments

    def descend(self):
        parent = self.parent
        children = self.children
        matched_segments = self.matched_segments
        path = self.path
        depth = self.depth
        # attempt to get the current path_segment; if there's an IndexError,
        # entire path except whether it ends with a slash has been matched
        try:
            path_segment = path[depth]
        except IndexError:
            # attempt to complete the match by comparing ends_with_slash
            if parent == path.ends_with_slash:
                # in most cases, children is a dict-of-dicts;
                # in this case, children are the match details
                path, resource, priority = children
                match = Match(path, resource, priority, matched_segments)
                return match, []
            # there is no match, and there are no additional potential matches 
            # that can be made against this path_to_match
            else:
                return mismatch, []
        # check if the parent matches the path, and if so then add
        # the children to a list of potential matches among the descendents
        potential_descendent_matches = []
        if parent == path_segment:
            matched_segments.append((parent, path_segment))
            depth += 1
            # all the chidren are potential matches
            for child in children:
                grandchildren = children[child]
                matched_segments_copy = copy_list(matched_segments)
                potential_match = PotentialMatch(path, child, grandchildren, 
                                                 depth, matched_segments_copy)
                potential_descendent_matches.append(potential_match)
            # additionally, if the parent is a PointySegment, the parent still
            # remains a potential match
            if isinstance(parent, paths.PointySegment):
                matched_segments_copy = copy_list(matched_segments)
                potential_match = PotentialMatch(path, parent, children, 
                                                 depth, matched_segments_copy)
                potential_descendent_matches.append(potential_match)
        return mismatch, potential_descendent_matches


class RouteKeyError(KeyError):

    pass


class RouteDuplicateError(KeyError):

    pass


class Routes(collections.MutableMapping):

    def __init__(self, cache=1e6, raise_on_duplicate=False):
        self._routes = {}
        self._routes[True] = {}
        self._routes[False] = {}
        self._paths = []
        self._current_priority = 0
        # setup cache
        if not isinstance(cache, (int, float, type(None))):
            raise TypeError()
        if cache is None:
            self.__cache = None
        else:
            self.__cache = caching.LRUCache(cache)
        # whether to raise an exception on a duplicate
        self.raise_on_duplicate = raise_on_duplicate

    def __getitem__(self, key):
        # pre-process inputs
        if isinstance(key, (str, unicode)):
            path = paths.Path.from_path(key)
        elif isinstance(key, (paths.Path, )):
            path = key
        # traverse nodes
        branch = self._routes[path.starts_with_slash]
        try:
            for segment in path:
                branch = branch[segment]
            _, resource, _ = branch[path.ends_with_slash]
        except KeyError:
            raise RouteKeyError()
        return resource

    def __setitem__(self, key, value):
        # pre-process inputs
        if isinstance(value, (Routes, )):
            routes_to_set = value
            base_path = paths.Path.from_path(key)
            paths_to_set = []
            resources_to_set = []
            #for relative_path_string in routes_to_set:
            for relative_path in routes_to_set._paths:
                path = base_path + relative_path
                resource = routes_to_set[relative_path]
                paths_to_set.append(path)
                resources_to_set.append(resource)
        else:
            paths_to_set = [paths.Path.from_path(key), ]
            resources_to_set = [value, ]
        # iteratively add paths and resources
        for path, resource in zip(paths_to_set, resources_to_set):
            # traverse nodes
            branch = self._routes[path.starts_with_slash]
            for segment in path:
                try:
                    branch = branch[segment]
                except KeyError:
                    branch[segment] = branch = {}
            # remove any previously set path from keys
            path_previously_set = path.ends_with_slash in branch
            if path_previously_set:
                if self.raise_on_duplicate:
                    raise RouteDuplicateError()
                previously_set_path, _, _ = branch[path.ends_with_slash]
                self._paths.remove(previously_set_path)
            # add new path
            self._paths.append(path)
            branch[path.ends_with_slash] = (path, resource, self._current_priority)
            self._current_priority += 1
        
    def __delitem__(self, key):
        # pre-process inputs
        path = paths.Path.from_path(key)
        branch = self._routes[path.starts_with_slash]
        # traverse nodes
        try:
            for segment in path:
                branch = branch[segment]
            del branch[path.ends_with_slash]
            self._paths.remove(path)
        except KeyError:
            raise RouteKeyError()

    def __iter__(self):
        self._paths.sort()
        return iter(map(str, self._paths))

    def __len__(self):
        return len(self._paths)

    @property
    def cache(self):
        return self.__cache

    def match(self, path_to_match_string):
        # check cache for *very* quick match
        if self.cache is not None:
            if path_to_match_string in self.cache:
                return self.cache[path_to_match_string]
        # no quick match unfortunately; pre-process input
        path_to_match = paths.VerbatimPath(path_to_match_string)
        # gather root potential matches
        starts_with_slash = path_to_match.starts_with_slash
        potential_matches = []
        for parent, children in self._routes[starts_with_slash].items():
            potential_match = PotentialMatch(path_to_match, parent, children)
            potential_matches.append(potential_match)
        # find best match
        best_match = Mismatch()
        while potential_matches:
            potential_match = potential_matches.pop()
            match, potential_descendent_matches = potential_match.descend()
            potential_matches.extend(potential_descendent_matches)
            if match > best_match:
                best_match = match
        # cache the match
        if self.cache is not None:
            self.cache[path_to_match_string] = best_match
        return best_match
