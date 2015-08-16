# standard libraries
import os
import collections
# third party libraries
pass
# first party libraries
pass


__all__ = ('VerbatimSegment', 'CurlySegment', 'PointySegment', 
           'Segment', 'Path', 'VerbatimPath', '__where__')
__where__ = os.path.dirname(os.path.abspath(__file__))


class VerbatimSegment(object):

    def __init__(self, value):
        self.__value = value
        self._hash = hash('VerbatimSegment({})'.format(self.value))

    @property
    def value(self):
        return self.__value

    def __hash__(self):
        return self._hash

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, VerbatimSegment):
            return self.value == other.value
        elif isinstance(other, (CurlySegment, PointySegment)):
            return True
        else:
            return NotImplemented


class CurlySegment(object):

    _hash = hash('CurlySegment')

    def __init__(self, alias):
        self.__alias = alias

    @property
    def alias(self):
        return self.__alias

    def __str__(self):
        return '{{}}'.format(self.alias)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, (CurlySegment, VerbatimSegment)):
            return True
        elif isinstance(other, PointySegment):
            return False
        else:
            return NotImplemented


class PointySegment(object):

    _hash = hash('PointySegment')

    def __init__(self, alias):
        self.__alias = alias

    @property
    def alias(self):
        return self.__alias

    def __str__(self):
        return '<{}>'.format(self.alias)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if isinstance(other, (PointySegment, VerbatimSegment)):
            return True
        elif isinstance(other, CurlySegment):
            return False
        else:
            return NotImplemented


class Segment(object):

    def __new__(cls, segment):
        if '/' in segment:
            raise ValueError()
        # handle special cases
        if len(segment) < 2:
            return VerbatimSegment(segment)
        # handle general cases
        starts_with = segment[0]
        ends_with = segment[-1]
        if starts_with == '{' and ends_with == '}':
            return CurlySegment(segment[1:-1])
        elif starts_with == '<' and ends_with == '>':
            return PointySegment(segment[1:-1])
        elif starts_with not in '{<' and ends_with not in '>}':
            return VerbatimSegment(segment)
        else:
            raise ValueError()


class Path(collections.Sequence):

    def __init__(self, path):
        self._path = path
        # define whether the path starts and ends with slash
        self._starts_with_slash = path.startswith('/')
        self._ends_with_slash = path.endswith('/') and len(path) > 1
        # define _segments, which this Sequence is aliased to
        naked_segments = path.lstrip('/').rstrip('/').split('/')
        self._segments = tuple(Segment(segment) for segment in naked_segments)
        # this is an immutable sequence and can be hashed
        self._hash = hash(self._segments)
        # construct an immutable tuple to be used for comparing against other paths
        # (primarily to provide a way to nicely sort a list of paths)
        # for more details, see __eq__
        self.__comparison_tuple = ((0, self.starts_with_slash), )
        for segment in self:
            if isinstance(segment, PointySegment):
                self.__comparison_tuple += ((4, segment.alias), )
            elif isinstance(segment, CurlySegment):
                self.__comparison_tuple += ((3, segment.alias), )
            elif isinstance(segment, VerbatimSegment):
                if segment.value != '':
                    self.__comparison_tuple += ((2, segment.value), )
                else:
                    self.__comparison_tuple += ((1, segment.value), )
            else:
                raise ValueError()
        self.__comparison_tuple += ((0, self.ends_with_slash), )
        # check for duplicates among unknown named segments; throw error
        # to prevent ambiguity if so
        unknown_segment_aliases = set()
        for segment in self:
            if isinstance(segment, (CurlySegment, PointySegment)):
                if segment.alias in unknown_segment_aliases:
                    raise ValueError()
                else:
                    unknown_segment_aliases.add(segment.alias)

    @property
    def starts_with_slash(self):
        return self._starts_with_slash

    @property
    def ends_with_slash(self):
        return self._ends_with_slash

    @property
    def path(self):
        return self._path

    def __str__(self):
        return self._path

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path)

    def __getitem__(self, item):
        return self._segments[item]

    def __len__(self):
        return len(self._segments)

    def __hash__(self):
        return self._hash

    @property
    def _comparison_tuple(self):
        return self.__comparison_tuple

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


class VerbatimPath(Path):

    def __init__(self, path):
        self._path = path
        # define whether the path starts and ends with slash
        self._starts_with_slash = path.startswith('/')
        self._ends_with_slash = path.endswith('/') and len(path) > 1
        # define _segments, which this Sequence is aliased to
        naked_segments = path.lstrip('/').rstrip('/').split('/')
        self._segments = tuple(VerbatimSegment(segment) for segment in naked_segments)
        # this is an immutable sequence and can be hashed
        self._hash = hash(self._segments)
        # construct an immutable tuple to be used for comparing against other paths
        # (primarily to provide a way to nicely sort a list of paths)
        # for more details, see __eq__
        self.__comparison_tuple = ((5, self.starts_with_slash), )
        for segment in self:
            if segment.value != '':
                self.__comparison_tuple += ((2, segment.value), )
            else:
                self.__comparison_tuple += ((1, segment.value), )
        self.__comparison_tuple += ((5, self.ends_with_slash), )
