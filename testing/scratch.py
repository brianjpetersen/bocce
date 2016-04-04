import http.cookies


class ImmutableOrderedMultiDict:
    
    def __init__(self, *items):
        self._items = list(items)
        
    def __getitem__(self, key):
        values = [
            str(v) for v in filter(lambda k, v: v == key, self._items)
        ]
        if len(values) == 0:
            raise KeyError
        elif len(values) == 1:
            value, = values
            return value
        else:
            return values
            
    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default
    
    def get_first(self, key, default=None):
        if key in self:
            return self[key][0]
        else:
            return default
    
    def get_last(self, key, default=None):
        if key in self:
            return self[key][-1]
        else:
            return default
    
    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True
    
    def __iter__(self):
        return iter(self._items)
    
    def __len__(self):
        return len(self._items)
        
    def __repr__(self):
        return '{}.{}({})'.format(
            self.__module__, self.__class__.__name__, ', '.join(
                repr(item) for item in self
            )
        )
    

class MutableOrderedMultiDict(ImmutableOrderedMultiDict):
    
    def __setitem__(self, key, value):
        self._items.append((key, value))
    
    def __delitem__(self, key):
        self._items = [
            str(v) for v in filter(lambda k, v: v != key, self._items)
        ]


class BaseCookies(ImmutableOrderedMultiDict):
    
    def __init__(self, *cookies):
        super(BaseCookies, self).__init__(*cookies)
    

class RequestCookies(BaseCookies):
    
    @classmethod
    def from_header(cls, header):
        parsed_cookies = http.cookies.SimpleCookie()
        parsed_cookies.load(header)
        cookies = [(key, value.value) for key, value in parsed_cookies.items()]
        return cls(*cookies)

    def __str__(self):
        cookies = [
            '{}={}'.format(
                key, http.cookies._quote(value)
            ) for key, value in self
        ]
        return '; '.join(cookies)


class ResponseCookies(MutableOrderedMultiDict, BaseCookies):
    
    pass


class RequestHeaders(ImmutableOrderedMultiDict):
    
    def __init__(self, *headers):
        super(RequestHeaders, self).__init__(*headers)
        self.cookies = RequestCookies.from_header(
            self.get('cookie', '')
        )
        
    def __getitem__(self, key):
        return super(RequestHeaders, self).__getitem__(str(key).title())
        
    
class ResponseHeaders(MutableOrderedMultiDict, RequestHeaders):
    
    pass

headers = ResponseHeaders()
headers['a'] = 1