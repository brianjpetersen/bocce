# standard libraries
import copy
# third party libraries
pass
# first party libraries
from . import (cookies, )


class RequestHeaders:
    
    def __init__(self, *items):
        self._headers = {}
        for key, value in items:
            key = str(key)
            titlecase_key = key.title()
            value = str(value)
            if titlecase_key not in self._headers:
                self._headers[titlecase_key] = []
            self._headers[titlecase_key].append(value)
        self.cookies = cookies.RequestCookies.from_header(
            self.get('cookie', '')
        )
    
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
        return cls(*items)
    
    def __iter__(self):
        for key in sorted(self.keys()):
            values = self._headers[key]
            for value in values:
                yield (key, value)
    
    def keys(self):
        return list(self._headers.keys())
    
    def items(self):
        return list(self)
        
    def __getitem__(self, key):
        titlecase_key = key.title()
        values = self._headers[titlecase_key]
        if len(values) == 1:
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
        return key.title() in self._headers
    
    def __len__(self):
        length = 0
        for _ in self:
            length += 1
        return length
    
    def __repr__(self):
        return '{}.{}{}'.format(
            self.__module__, self.__class__.__name__, tuple(self)
        )
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self
        )


class ResponseHeaders:

    def __init__(self, *items):
        self._headers = {}
        self.cookies = cookies.ResponseCookies()
        for key, value in items:
            self[key] = value
    
    def __setitem__(self, key, value):
        key = str(key)
        titlecase_key = key.title()
        value = str(value)
        if titlecase_key == 'Set-Cookie':
            self.cookies.set_from_header(value)
        else:
            if titlecase_key not in self._headers:
                self._headers[titlecase_key] = []
            self._headers[titlecase_key].append(value)
    
    def __getitem__(self, key):
        titlecase_key = str(key).title()
        if titlecase_key == 'Set-Cookie':
            return [str(cookie) for cookie in self.cookies.values()]
        else:
            values = self._headers[titlecase_key]
            if len(values) == 1:
                value, = values
                return value
            else:
                return values
    
    def keys(self):
        keys = list(self._headers.keys())
        if len(self.cookies) > 0:
            keys.append('Set-Cookie')
        return keys
        
    def __iter__(self):
        for key in sorted(self.keys()):
            if key == 'Set-Cookie':
                values = self.cookies.values()
            else:
                values = self._headers[key]
            for value in values:
                yield (key, value)
    
    def items(self):
        return list(self)
    
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
    
    def delete(self, key, index=None):
        titlecase_key = str(key).title()
        if titlecase_key != 'Set-Cookie':
            if index is None:
                self._headers[titlecase_key] = []
            elif isinstance(index, (int, slice)):
                values = self._headers[titlecase_key]
                del values[index]
            else:
                raise TypeError
        else:
            pass
    
    def __contains__(self, key):
        return key.title() in self._headers
    
    def __len__(self):
        length = 0
        for _ in self:
            length += 1
        return length
    
    def __repr__(self):
        return '{}.{}{}'.format(
            self.__module__, self.__class__.__name__, tuple(self)
        )
    
    def __str__(self):
        return '\n'.join(
            '{}: {}'.format(key, value) for key, value in self
        )
