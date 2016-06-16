# standard libraries
import os
import functools
import collections
import collections.abc
import datetime
import json
import multiprocessing
import threading
import traceback
import time
# third party libraries
pass
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))


class repeat(threading.Thread):
    
    def __init__(self, function, period, how='thread', on_error=None,
                 args=None, kwargs=None):
        super(repeat, self).__init__(daemon=True)
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if on_error is None:
            def on_error(exception):
                traceback.print_exc()
                print()
        def wrapped():
            try:
                function(*args, **kwargs)
            except Exception as exception:
                on_error(exception)
        self.function = wrapped
        self.period = period
        if how == 'thread':
            self.How = threading.Thread
        elif how == 'process':
            self.How = multiprocessing.Process
        self.terminated = False
        self.start()
            
    def run(self):
        while self.terminated == False:
            try:
                start = time.time()
                runner = self.How(target=self.function)
                runner.start()
                runner.join()
                duration = time.time() - start
                if duration < self.period:
                    time.sleep(self.period - duration)
            except:
                continue
    
    def terminate(self):
        self.terminated = True


def cached_getter(allow_get=True, allow_set=True, allow_delete=True):
    
    class Wrapper:
        
        __slots__ = ('getter', 'name', 'cached_name', )
        
        def __init__(self, getter):
            self.getter = getter
            self.name = getter.__name__
            self.cached_name = '_cached_{}'.format(self.name)
        
        def __get__(self, instance, owner=None):
            if self.allow_get == False:
                raise AttributeError
            try:
                return getattr(instance, self.cached_name)
            except:
                value = self.getter(instance)
                setattr(instance, self.cached_name, value)
                return value
        
        def __set__(self, instance, value):
            if self.allow_set == False:
                raise AttributeError
            setattr(instance, self.cached_name, value)
        
        def __delete__(self, instance):
            if self.allow_delete == False:
                raise AttributeError
            delattr(instance, self.cached_name)
    
    Wrapper.allow_get = allow_get
    Wrapper.allow_set = allow_set
    Wrapper.allow_delete = allow_delete
    
    return Wrapper


"""
def cached_setter(allow_get=True, set_once=False, allow_delete=True):
    
    class Wrapper:
        
        __slots__ = ('name', 'setter', 'was_set', 'value', )
        
        def __init__(self, setter):
            self.setter = setter
            self.name = setter.__name__
            self.was_set = False
        
        def __get__(self, obj, type=None):
            if self.allow_get == False:
                raise AttributeError
            return self.value
        
        def __set__(self, obj, value):
            if self.was_set and self.set_once:
                raise AttributeError
            self.value = self.setter(obj, value)
        
        def __delete__(self, obj):
            if self.allow_delete == False:
                raise AttributeError
            delattr(obj, self.name)
            
    Wrapper.allow_get = allow_get
    Wrapper.allow_delete = allow_delete
    Wrapper.set_once = set_once
    
    return Wrapper
"""


def once(f):
    
    @functools.wraps(f)
    def decorator(*args, **kwargs):
        try:
            return f._result
        except AttributeError:
            result = f._result = f(*args, **kwargs)
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


class When:
    
    @staticmethod
    def timestamp(when=None, format='%Y-%m-%dT%H:%M:%SZ'):
        if when is None:
            when = datetime.datetime.utcnow()
        return when.strftime(format)
    
    @staticmethod
    def iso_timestamp(when=None):
        return When.timestamp(when, format='%Y-%m-%dT%H:%M:%SZ')
    
    @staticmethod
    def unix_timestamp(when=None):
        if when is None:
            when = datetime.datetime.utcnow()
        return when.timestamp()
    
    @staticmethod
    def http_timestamp(when=None):
        return When.timestamp(when, format='%a, %d-%b-%Y %T GMT')
    
    """
    @staticmethod
    def from_timestamp(timestamp, format='YYYY-MM-DD'):
        pass
    """


class JsonEncoder(json.JSONEncoder):
    
    def __init__(self, indent=None, serializers=None):
        super(JsonEncoder, self).__init__(indent=indent)
        if serializers is None:
            serializers = {}
        self.serializers = serializers
    
    def default(self, obj):
        try:
            serializer = self.serializers[obj.__class__]
            return serializer(obj)
        except:
            return super(JsonEncoder, self).default(obj)
