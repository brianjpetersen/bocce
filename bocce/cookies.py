""" Technically, there can be multiple cookies with the same name;
    however, this is insane and is not supported here.

"""
# standard libraries
import os
import collections.abc
import collections
import http.cookies
# third party libraries
pass
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))


class RequestCookies(collections.abc.Mapping):
    
    def __init__(self, **cookies):
        self._cookies = cookies
    
    @classmethod
    def from_header(cls, header):
        parsed_cookies = http.cookies.SimpleCookie()
        parsed_cookies.load(header)
        cookies = {key: value.value for key, value in parsed_cookies.items()}
        return cls(**cookies)
    
    def __getitem__(self, key):
        return self._cookies[key]
    
    def __iter__(self):
        return iter(self._cookies)
    
    def __len__(self):
        return len(self._cookies)
    
    def __str__(self):
        return '; '.join(
            '{}={}'.format(
                key, http.cookies._quote(value)
            ) for key, value in self.items()
        )
    
    def __repr__(self):
        return '{}.{}({})'.format(
            self.__module__, self.__class__.__name__, ', '.join(
                "{}='{}'".format(key, value) for key, value in self.items()
            )
        )


class ResponseCookie:
    
    def __init__(self, key, value='', max_age=None, expires=None, path=None,
                 domain=None, secure=False, http_only=False):
        self.key = key
        self.value = value
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.http_only = http_only
    
    def __repr__(self):
        return '{}.{}({})'.format(
            self.__module__, self.__class__.__name__, ', '.join(
                '{}={}'.format(name, repr(getattr(self, name))) for name in (
                    'key', 'value', 'max_age', 'expires', 'path', 'domain', 
                    'secure', 'http_only',
                )
            )
        )
    
    def __str__(self):
        key = self.key
        if self.value is not None:
            value = self.value
        else:
            value = ''
        cookie_segments = ['{}={}'.format(key, value), ]
        if self.max_age is not None:
            cookie_segments.append('Max-Age={}'.format(self.max_age))
        if self.expires is not None:
            cookie_segments.append(
                'Expires={:%a, %d-%b-%Y %T GMT}'.format(self.expires)
            )
        if self.path is not None:
            cookie_segments.append('Path={}'.format(self.path))
        if self.domain is not None:
            cookie_segments.append('Domain={}'.format(self.domain))
        if self.secure:
            cookie_segments.append('Secure')
        if self.http_only:
            cookie_segments.append('HttpOnly')
        return '; '.join(cookie_segments)


class ResponseCookies(collections.abc.MutableMapping):
    
    def __init__(self, *cookies):
        self._cookies = collections.OrderedDict(
            (cookie.key, cookie) for cookie in cookies
        )
    
    def set(self, key, value='', max_age=None, expires=None, path=None, 
            domain=None, secure=False, http_only=False):
        self[key] = ResponseCookie(
            key, value, max_age, expires, path, domain, secure, http_only
        )
    
    def set_from_header(self, cookie):
        raise NotImplementedError
    
    def __getitem__(self, key):
        return self._cookies[key]
    
    def __delitem__(self, key):
        del self._cookies[key]
    
    def __iter__(self):
        return iter(self._cookies)
    
    def __len__(self):
        return len(self._cookies)
    
    def __setitem__(self, key, value):
        if isinstance(value, ResponseCookie):
            self._cookies[key] = value
        else:
            self.set(key, value)
    
    @property
    def headers(self):
        return [('Set-Cookie', str(cookie)) for cookie in self.values()]
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self.headers
        )
    
    def __repr__(self):
        return '{}.{}({})'.format(
            self.__module__, self.__class__.__name__, ', '.join(
                (repr(cookie) for cookie in self.values())
            )
        )
