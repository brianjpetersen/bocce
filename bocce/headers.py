# standard libraries
pass
# third party libraries
pass
# first party libraries
pass


class Immutable:
    
    __slots__ = ('_items', '_dict', )
    
    def __init__(self, items=None):
        if items is None:
            items = []
        self._items = [(str(key), str(value)) for key, value in items]
        self._dict = {}
        for key, value in self._items:
            if key not in self._dict:
                self._dict[key.lower()] = []
            self._dict[key.lower()].append((key, value))
    
    @classmethod
    def from_environment(cls, environment):
        items = []
        if 'CONTENT_LENGTH' in environment:
            items.append(('Content-Length', environment['CONTENT_LENGTH']))
        if 'CONTENT_TYPE' in environment:
            items.append(('Content-Type', environment['CONTENT_TYPE']))
        for key, value in environment.items():
            if key.startswith('HTTP_'):
                if key == 'HTTP_CONTENT_LENGTH' and 'CONTENT_LENGTH' in environment:
                    continue
                if key == 'HTTP_CONTENT_TYPE' and 'CONTENT_TYPE' in environment:
                    continue
                key = key[5:].replace('_', '-').title()
                items.append((key, value))
        return cls(items)
    
    def __getitem__(self, key):
        _, value = self._dict[key.lower()]
        return value
    
    def __iter__(self):
        return iter(self._items)
    
    def __contains__(self, key):
        return key in self._dict
    
    def keys(self):
        for key, _ in self.items():
            yield key
    
    def values(self):
        for _, value in self.items():
            yield value
    
    def items(self):
        return self._items
    
    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default
    
    def __eq__(self, other):
        return self._items == other._items
    
    def __ne__(self, other):
        return self._items != other._items
    
    def __len__(self):
        return len(self._items)
    
    def copy(self):
        return copy.deepcopy(self)
    
    def get_first(self, key, default=None):
        if key in self._dict.keys():
            return self._dict[key][0]
        else:
            return default
    
    def get_last(self, key, default=None):
        if key in self._dict.keys():
            return self._dict[key][-1]
        else:
            return default
        
    def get_all(self, key):
        return self.get(key, [])
    
    def __repr__(self):
        return '{}.{}{}'.format(
            self.__module__, self.__class__.__name__, tuple(self._items)
        )
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self
        )
    
    def __getnewargs__(self):
        return (self._items, )


class Mutable(Immutable):
    
    def __setitem__(self, key, value):
        item = (key, value)
        self._dict[key.lower()].append(item)
        self._items.append(item)
        
    def __delitem__(self, key):
        del self._dict[key.lower()]
        self._items = [
            (k, v) for k, v in self._items if k.lower() != key.lower()
        ]
    
    def pop(self, key, default=None):
        if key not in self and default is None:
            raise KeyError
        value = self[key]
        del self[key]
        return value
    
    def update(self, other):
        for key, value in other.items():
            self[key] = value
