# standard libraries
import os
import collections
# third party libraries
pass
# first party libraries
pass


__all__ = ('LeastRecentlyUsed', )
__where__ = os.path.dirname(os.path.abspath(__file__))


class LeastRecentlyUsed(collections.MutableMapping):

    def __init__(self, size=None):
        if not isinstance(size, (int, float)):
            raise TypeError()
        else:
            if size < 0:
                raise ValueError()
        self.size = size
        self.__cache = collections.OrderedDict()

    def __getitem__(self, key):
        return self.touch(key)

    @property
    def overflowing(self):
        return len(self) > self.size

    def touch(self, key):
        value = self.__cache.pop(key)
        self.__cache[key] = value
        return value

    def __setitem__(self, key, value):
        self.__cache[key] = value
        if self.size is not None:
            while self.overflowing:
                self.__cache.popitem(last=False)

    def __delitem__(self, key):
        del self.__cache[key]

    def __iter__(self):
        return iter(self.__cache)

    def __len__(self):
        return len(self.__cache)
