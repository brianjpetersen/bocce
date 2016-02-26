# standard libraries
import os
import re
import copy
import collections.abc
import urllib.parse
import threading
import copy
# third party libraries
pass
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))


class _TopLevelDomains(collections.abc.MutableSet):
    """ A private set-like object for curating top-level domains.
    
        Note, although this essentially acts as a set, it works to cache
        the regular expression pattern upon first access.
    
    """
    def __init__(self):
        self._set = set(('com', 'org', 'net', 'edu', 'gov', 'mil', ))
        self._pattern = None
    
    def __contains__(self, top_level_domain):
        return top_level_domain in self._set
        
    def __iter__(self):
        return self._set.__iter__()
        
    def __len__(self):
        return len(self._set)
        
    def add(self, top_level_domain):
        self._pattern = None
        return self._set.add(top_level_domain)
        
    def discard(self, top_level_domain):
        self._pattern = None
        return self._set.discard(top_level_domain)
    
    def __repr__(self):
        return repr(self._set)
        
    def __str__(self):
        return str(self._set)
    
    @property
    def re(self):
        if self._pattern is None:
            top_level_domains = sorted(self._set, key=lambda d: (-len(d), d))    
            top_level_domains = '|'.join(top_level_domains)
            regex = (
                '(?P<subdomains>.+?)(\.(?P<top_level_domain>{}))?\Z'
            ).format(top_level_domains)
            self._pattern = re.compile(regex)
        return self._pattern


top_level_domains = _TopLevelDomains()


def split_host(host):
    """ Split host into subdomains, domain, and top-level domain.
    
        Relies on definition of ```top_level_domains``` which is accessible
        at the module-level.
    
    """
    match = top_level_domains.re.match(host)
    if match is None:
        return (None, None, None)
    else:
        match = match.groupdict()
        domain_and_subdomains = match['subdomains'].split('.')
        top_level_domain = match['top_level_domain']
        subdomains = tuple(domain_and_subdomains[:-1])
        domain = domain_and_subdomains[-1]
        return (subdomains, domain, top_level_domain, )


_scheme_regex = (
    '(?P<scheme>.+?)'
    '\\:\\/\\/' # this isn't strictly correct, but allows for naked authorities
)

_authority_regex = (
    '(' # optional authentication
        '(' # user
            '(?P<user>.+?)'
        ')'
        '(' # optional password
            '\\:'
            '(?P<password>.+?)'
        ')?' # password is optional
        '\\@'
    ')?' # authentication is optional
    '(' # host
        '(?P<host>.+?)'
    ')' # host is required if authority is present
    '(' # optional port
        '\\:'
        '(?P<port>\d+?)'
    ')?' # port is optional
)

_path_regex = (
    '\\/'
    '(?P<path>.+?)'
)

_query_string_regex = (
    '\\?'
    '(?P<query_string>.+?)'
)

_fragment_regex = (
    '\\#'
    '(?P<fragment>.+?)'
)

_url_regex = (
    '('
        + _scheme_regex +
    ')?'
    '('
        + _authority_regex +
    ')?'
    '('
        + _path_regex +
    ')?'
    '('
        + _query_string_regex +
    ')?'
    '('
        + _fragment_regex +
    ')?'
    '\Z'
)

_url_pattern = re.compile(_url_regex)


def split_url(url):
    """ Split a URL string into a dictionary of constituent string components.
        
        Note, this implementation favors pragmatism to correctness and deviates 
        from the spec in a few ways.  For example, while IETF RFC 7595 
        requires the scheme be defined, it is a common use case to exclude it.
        This allows naked authorities, like www.google.com, to be parsed
        correctly.
        
        The following template is used for parsing URLs, where brackets indicate
        optional components:
        
        [scheme:[//]][[user[:password]@]host[:port]][[/]path]
            [?query_string][#fragment]
        
    """
    try:
        match = _url_pattern.match(url.strip()).groupdict()
    except:
        raise ValueError('Unable to parse URL {}.'.format(url))
    return match


def construct_url(host=None, path=None, scheme=None, query_string=None,
                  port=None, fragment=None, user=None, password=None,
                  quote=False):
    if quote:
        host = urllib.parse.quote(host, safe='')
        path = urllib.parse.quote(path)
        scheme = urllib.parse.quote(scheme, safe='+')
        query_string = urllib.parse.quote(query_string, safe='=&;')
        fragment = urllib.parse.quote(fragment, safe='!#=&;')
        user = urllib.parse.quote(user, safe='')
        password = urllib.parse.quote(password, safe='')
    url = ''
    if scheme is not None:
        url += '{}://'.format(scheme)
    if user is not None:
        url += user
        if password is not None:
            url += ':{}'.format(password)
        url += '@'
    if host is not None:
        url += host
    if port is not None:
        if port == 80 and scheme == 'http':
            pass
        elif port == 443 and scheme == 'https':
            pass
        else:
            url += ':{}'.format(port)
    if path is not None:
        if path.startswith('/'):
            url += path
        else:
            url += '/{}'.format(path)
    if query_string is not None:
        url += '?{}'.format(query_string)
    if fragment is not None:
        url += '#{}'.format(fragment)
    return url
    

class QueryString(collections.abc.MutableMapping):
    """ A mutable ordered multi-dict for representing query strings.
        
        >>> query_string = QueryString.from_string('a=1&b=2&c=3')
        >>> query_string['a']
        '1'
        >>> str(query_string)
        'a=1&b=2&c=3'
        
        >>> query_string = QueryString.from_string('a=1&b=2&a=3')
        >>> query_string['a']
        ['1', '3']
        >>> query_string.get_first('a')
        '1'
        >>> query_string.get_last('a')
        '3'
        
    """
    _separator_regex = re.compile(re.escape('&') + '|' + re.escape(';'))
    
    def __init__(self, items=[], separator='&', quote=False):
        self.separator = separator
        self.quote = quote
        self._dict = {}
        self._items = []
        for key, value in items:
            self[key] = value
    
    @classmethod
    def from_string(cls, query_string, separator='&', unquote=True):
        if query_string is None:
            return cls([], separator, not unquote)
        if unquote:
            query_string = urllib.parse.unquote(query_string)
        components = cls._separator_regex.split(query_string)
        items = []
        for component in components:
            if '=' in component:
                key, value = component.split('=')
            else:
                key, value = component, None
            items.append((key, value))
        return cls(items, separator, not unquote)
    
    def __getitem__(self, key):
        value = self._dict[key]
        if len(value) == 1:
            return value[0]
        else:
            return value
        
    def __setitem__(self, key, value):
        with threading.Lock() as lock:
            if key not in self._dict:
                self._dict[key] = []
            self._dict[key].append(str(value))
            self._items.append((key, str(value)))
            
    def __delitem__(self, key):
        with threading.Lock() as lock:
            del self._dict[key]
            self._items = [(k, v) for k, v in self._items if k != key]
        
    def __iter__(self):
        return self._dict.__iter__()
        
    def __len__(self):
        return len(self._dict)
    
    def __repr__(self):
        return '{}{}'.format(
            self.__class__.__name__, 
            tuple((k, v) for k, v in self._items)
        )
    
    def __str__(self):
        string_list = []
        for key, value in self._items:
            if self.quote:
                key = urllib.parse.quote(key, safe='')
                value = urllib.parse.quote(value, safe='')
            if value is None:
                string_list.append(key)
            else:
                string_list.append('='.join((key, value)))
        return self.separator.join(string_list)
    
    def copy(self):
        return copy.copy(self)
    
    def get_first(self, key):
        return self._dict[key][0]
    
    def get_last(self, key):
        return self._dict[key][-1]


class Url: # tk derive from tuple to make immutable?
    
    def __init__(self, host=None, path=None, scheme=None, query_string=None,
                 port=None, fragment=None, user=None, password=None, 
                 quote=False):
        self.quote = quote
        self._scheme = scheme
        self._user = user
        self._password = password
        self._host = host
        self._subdomains, self._domain, self._top_level_domain = split_host(host)
        self._port = port
        if port is None:
            self._processed_port = port
        else:
            self._processed_port = int(port)
        self._path = path
        if path is None:
            self._processed_path = None
        else:
            self._processed_path = path.lstrip('/ ').rstrip()
        self._query_string = query_string
        if query_string is None:
            self._processed_query_string = query_string
        elif isinstance(query_string, collections.abc.Mapping):
            self._processed_query_string = QueryString(query_string.items())
        elif isinstance(query_string, (str, bytes, )):
            self._processed_query_string = QueryString.from_string(
                self._query_string
            )
        else:
            raise TypeError('Variable query_string must be either string-like \
                             or dict-like')
        self._fragment = fragment
        self._components = collections.OrderedDict([
            ('host', host),
            ('path', path),
            ('scheme', scheme),
            ('query_string', query_string),
            ('port', port),
            ('fragment', fragment),
            ('user', user),
            ('password', password),
        ])
    
    @property
    def scheme(self):
        return self._scheme
        
    @property
    def user(self):
        return self._user
        
    @property
    def password(self):
        return self._password
    
    @property
    def host(self):
        return self._host
    
    @property    
    def subdomains(self):
        return self._subdomains
    
    @property
    def domain(self):
        return self._domain
    
    @property
    def top_level_domain(self):    
        return self._top_level_domain
    
    @property
    def port(self):
        return self._processed_port
    
    @property
    def path(self):
        return self._processed_path
    
    @property
    def query_string(self):
        return self._processed_query_string.copy()
    
    @property
    def fragment(self):
        return self._fragment
    
    @classmethod
    def from_string(cls, url_string):
        url_components = split_url(url_string.strip())
        return cls(**url_components)
    
    def replace(self, **replacements):
        cls = self.__class__
        url_components = self._components.copy()
        url_components.update(replacements)
        return cls(**url_components)
    
    def __repr__(self):
        return '{}{}'.format(
            self.__class__.__name__, 
            tuple(self._components.values()) + (self.quote, )
        )
    
    def __str__(self):
        return construct_url(quote=self.quote, **self._components)
