# standard libraries
import os
import functools
import collections.abc
import datetime
# third party libraries
pass
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))


def once(f):
    
    @functools.wraps(f)
    def decorator(*args, **kwargs):
        try:
            return f._result
        except AttributeError:
            result = f(*args, **kwargs)
            f._result = copy.deepcopy(result)
            return result
    
    return decorator
    
    
class LRUCache(collections.abc.MutableMapping):

    def __init__(self, size=None):
        if not isinstance(size, (int, float)):
            raise TypeError()
        else:
            if size < 0:
                raise ValueError()
        self._size = size
        self._cache = collections.OrderedDict()

    def __getitem__(self, key):
        return self.touch(key)
    
    def flush(self):
        self._cache = collections.OrderedDict()

    @property
    def overflowing(self):
        return len(self) > self.size

    def touch(self, key):
        value = self._cache.pop(key)
        self._cache[key] = value
        return value

    def __setitem__(self, key, value):
        self._cache[key] = value
        if self.size is not None:
            self.squeeze()
            
    @property
    def size(self):
        return self._size
        
    @size.setter
    def size(self, size):
        self._size = size
        self.squeeze()
            
    def squeeze(self):
        while self.overflowing:
            self._cache.popitem(last=False)

    def __delitem__(self, key):
        del self._cache[key]

    def __iter__(self):
        return iter(self._cache)

    def __len__(self):
        return len(self._cache)


def timestamp(when=None, format='%Y-%m-%dT%H:%M:%SZ'):
    if when is None:
        when = datetime.datetime.utcnow()
    return when.strftime(format)
