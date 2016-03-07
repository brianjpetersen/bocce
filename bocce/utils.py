# standard libraries
import os
import functools
import collections
import collections.abc
import datetime
import copy
# third party libraries
pass
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))


def cached_getter(allow_get=True, allow_set=True, allow_delete=True):
    
    class Wrapper:
        
        __slots__ = ('getter', 'name', 'value', )
    
        def __init__(self, getter):
            self.getter = getter
            self.name = getter.__name__
    
        def __get__(self, obj, type=None):
            if self.allow_get == False:
                raise AttributeError
            try:
                return self.value
            except:
                self.value = self.getter(obj)
                return self.value
    
        def __set__(self, obj, value):
            if self.allow_set == False:
                raise AttributeError
            self.value = value
    
        def __delete__(self, obj):
            if self.allow_delete == False:
                raise AttributeError
            delattr(obj, self.name)
    
    Wrapper.allow_get = allow_get
    Wrapper.allow_set = allow_set
    Wrapper.allow_delete = allow_delete
    
    return Wrapper


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

    def timestamp(when=None, format='%Y-%m-%dT%H:%M:%SZ'):
        if when is None:
            when = datetime.datetime.utcnow()
        return when.strftime(format)
    
    def from_timestamp(timestamp, format='YYYY-MM-DD'):
        pass






class RequiredArg: pass

def by_index(index):
    
    @property
    def getter(self):
        return tuple.__getitem__(self, index)
    
    return getter

def delete_inherited_attribute(attribute_name):
    
    @property
    def raise_attribute_error(self):
        raise AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__,
                attribute_name,
            )
        )
    
    return raise_attribute_error

def named_tuple(*args, **kwargs):
    
    fields = {}
    for key in args:
        if not isinstance(key, str):
            raise TypeError('Field names must be type str.')
        fields[key] = RequiredArg
    for key in kwargs:
        if not isinstance(key, str):
            raise TypeError('Field names must be type str.')
        default = kwargs[key]
        fields[key] = default
    fields = collections.OrderedDict(sorted(fields.items()))
    
    def inner(cls):
        
        def __new__(cls, **kwargs):
            # check to make sure required keys passed in
            required_keys = (key for key, value in cls.__fields__.items() if value == RequiredArg)
            missing_keys = []
            for key in required_keys:
                if key not in kwargs:
                    missing_keys.append(key)
            if len(missing_keys) > 0:
                raise TypeError("'{}' object missing {} required {}: {}".format(
                        cls.__name__,
                        len(missing_keys),
                        'argument' if len(missing_keys) == 1 else 'arguments',
                        'and '.join("'{}'".format(key) for key in missing_keys)
                    )
                )
            # check to make sure no extraneous keys
            extraneous_keys = []
            for key in kwargs:
                if key not in cls.__fields__:
                    extraneous_keys.append(key)
            if len(extraneous_keys) > 0:
                raise TypeError("'{}' object has {} extraneous {}: {}".format(
                        cls.__name__,
                        len(extraneous_keys),
                        'argument' if len(extraneous_keys) == 1 else 'arguments',
                        'and '.join("'{}'".format(key) for key in extraneous_keys)
                    )
                )
            # return tuple object
            fields = copy.deepcopy(cls.__fields__)
            fields.update(kwargs)
            return tuple.__new__(cls, tuple(value for value in fields.values()))
        
        def __repr__(self):
            if self.__module__ == '__main__':
                module = ''
            else:
                module = '{}.'.format(self.__module__)
            arguments = []
            for key in self.__fields__:
                value = getattr(self, key)
                arguments.append('{}={}'.format(key, repr(value)))
            arguments = ', '.join(arguments)
            class_name = self.__class__.__name__
            return '{}{}({})'.format(module, class_name, arguments)
        
        def __getnewargs__(self):
            return {
                key: tuple.__getitem__(self, index) for index, key in enumerate(self.__fields__)
            }
        
        def __getitem__(self, item):
            raise TypeError("'{}' object does not support indexing".format(self.__class__.__name__))
            
        def __dir__(self):
            return [
                d for d in tuple.__dir__(self) if (d not in ('count', 'index') or d in self.__fields__)
            ]
        
        attributes = {
            '__slots__': (),
            '__new__': __new__,
            '__getnewargs_ex__': __getnewargs__,
            '__fields__': fields,
            '__repr__': __repr__,
            '__getitem__': __getitem__,
            'count': delete_inherited_attribute('count'),
            'index': delete_inherited_attribute('index'),
            '__dir__': __dir__,
        }
        for index, key in enumerate(fields):
            attributes[key] = by_index(index)
        for key, value in cls.__dict__.items():
            if key.startswith('__') and key.endswith('__'):
                continue
            attributes[key] = value
        
        __bases__ = cls.__bases__
        if __bases__[0] == object:
            __bases__ = __bases__[1:]
        __bases__ = (tuple, ) + __bases__
        
        return type(cls.__name__, __bases__, attributes)
    
    return inner
