# standard libraries
import os
import re
# third party libraries
import requests
# first party libraries
pass


__where__ = os.path.dirname(os.path.abspath(__file__))
__all__ = ('__where__', 'Url', )


def dump_top_level_domains():
    response = requests.get('https://publicsuffix.org/list/public_suffix_list.dat')
    top_level_domains = response.text
    with open(os.path.join(__where__, '.top-level-domains.dat'), 'wb') as f:
        f.write(top_level_domains.encode('utf-8'))
    return top_level_domains


def compile_top_level_domain_regex():
    """
    try:
        with open(os.path.join(__where__, '.top-level-domains.dat'), 'rb') as f:
            raw = f.read().decode('utf-8')
    except:
        raw = dump_top_level_domains()
    top_level_domains = []
    for top_level_domain in raw.splitlines():
        top_level_domain = top_level_domain.strip().lower()
        is_comment = top_level_domain.startswith('//') or top_level_domain == ''
        if is_comment:
            continue
        try:
            top_level_domain = re.escape('{}'.format(top_level_domain)).replace('*', '.+?')
        except UnicodeEncodeError:
            continue
        top_level_domains.append(top_level_domain)
    top_level_domains.sort(key=lambda domain: (-len(domain), domain))
    top_level_domains = '|'.join(top_level_domains)
    """
    top_level_domains = 'com|org|net|edu|gov|mil'
    regex = '(?P<subdomains>.+?)(\.(?P<top_level_domain>{}))?\Z'.format(top_level_domains)
    return re.compile(regex)

COMPILED_DOMAIN_REGEX = compile_top_level_domain_regex()

# TK: should really scrub for invalid components
# TK: should handle url percent encoding
URL_REGEX = (
    # scheme
    '('
        '(?P<scheme>'
            '.+?'
        ')'
        '\:\/\/'
    ')?' # optional
    # username/password
    '('
        '(?P<username>'
            '.+?' # at least one character for username
        ')?'
        '('
            '\:' # ampersand to separate host
            '(?P<password>'
                '.+?' # if password included, a : followed by at least one 
            ')'
        ')?'
        '\@' # ampersand to separate host
    ')?' # optional
    # host
    '(?P<host>'
        '.+?'
    ')' # required
    # port
    '(?P<port>'
        '\d+?'
    ')?'
    # path
    '(?P<path>'
        '\/.*?'
    ')?' # optional
    # query_string
    '('
        '\?'
        '(?P<query_string>'
            '.+?'
        ')'
    ')?' # optional
    # fragment
    '('
        '\#!?'
        '(?P<fragment>'
            '.+?'
        ')'
    ')?' # optional
    '\Z'
)


URL_PATTERN = re.compile(URL_REGEX)


def split_domains(host):
    match = COMPILED_DOMAIN_REGEX.match(host).groupdict()
    domain_and_subdomains = match['subdomains'].split('.')
    return match['top_level_domain'], tuple(domain_and_subdomains[:-1]), domain_and_subdomains[-1]


def if_none(value, default):
    if value is None:
        return default
    else:
        return value


def parse_url(url):
    """

        >>> parse_url('http://example.com') == {
        ...     'host': 'example.com', 
        ...     'query_string': '', 
        ...     'path': '/',
        ...     'fragment': '', 
        ...     'scheme': 'http', 
        ...     'port': None,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://example.com/') == {
        ...     'host': 'example.com',
        ...     'query_string': '',
        ...     'path': '/', 
        ...     'fragment': '',
        ...     'scheme': 'http',
        ...     'port': None,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://example.com/a/b/c') == {
        ...     'host': 'example.com',
        ...     'query_string': '',
        ...     'path': '/a/b/c', 
        ...     'fragment': '',
        ...     'scheme': 'http',
        ...     'port': None,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://example.com/a/b/c/') == {'host': 'example.com', 
        ...     'query_string': '', 
        ...     'path': '/a/b/c/', 
        ...     'fragment': '',
        ...     'scheme': 'http',
        ...     'port': None,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://example.com/a/b/c?query-string#fragment') == {
        ...     'fragment': 'fragment',
        ...     'host': 'example.com',
        ...     'query_string': 'query-string', 
        ...     'path': '/a/b/c',
        ...     'scheme': 'http',
        ...     'port': None,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://example.com:8080/a/b/c#!fragment') == {
        ...     'fragment': 'fragment', 
        ...     'host': 'example.com:',
        ...     'query_string': '',
        ...     'path': '/a/b/c',
        ...     'scheme': 'http',
        ...     'port': 8080,
        ...     'username': None,
        ...     'password': None,
        ... }
        True
        >>> parse_url('http://username:password@example.com:8080/a/b/c#!fragment') == {
        ...     'fragment': 'fragment', 
        ...     'host': 'example.com:',
        ...     'query_string': '',
        ...     'path': '/a/b/c',
        ...     'scheme': 'http',
        ...     'port': 8080,
        ...     'username': 'username',
        ...     'password': 'password',
        ... }
        True
        >>> parse_url('http://username@example.com:8080/a/b/c#!fragment') == {
        ...     'fragment': 'fragment', 
        ...     'host': 'example.com:',
        ...     'query_string': '',
        ...     'path': '/a/b/c',
        ...     'scheme': 'http',
        ...     'port': 8080,
        ...     'username': 'username',
        ...     'password': None,
        ... }
        True

    """
    match = URL_PATTERN.match(url).groupdict()
    url_parts = {}
    url_parts['scheme'] = if_none(match.get('scheme'), '')
    url_parts['host'] = match.get('host')
    url_parts['port'] = match.get('port')
    if url_parts['port'] is not None:
       url_parts['port'] = int(url_parts['port']) 
    url_parts['path'] = if_none(match.get('path'), '/')
    url_parts['query_string'] = if_none(match.get('query_string'), '')
    url_parts['fragment'] = if_none(match.get('fragment'), '')
    url_parts['username'] = match.get('username')
    url_parts['password'] = match.get('password')
    return url_parts


class Url(object):
    """ A friendly alternative to urllib.urlparse.

        >>> url = Url('http', 'www.podimetrics.com')
        >>> print(url)
        http://www.podimetrics.com/
        >>> url.domain
        'podimetrics'
        >>> url.subdomains == ('www', )
        True
        >>> url.top_level_domain
        'com'
        >>> url.replace(path='a/path', port=None).url
        'http://www.podimetrics.com/a/path'

    """
    def __init__(self, scheme='http', host='localhost', port=80, path='/', 
                 query_string='', fragment='', username=None, password=None):
        self.scheme = scheme.lower()
        self.host = host.lower()
        self.port = port
        if path.startswith('/') == False or path == '':
            path = '/' + path
        self.path = path
        self.query_string = query_string
        self.fragment = fragment
        self.username = username
        self.password = password
        if self.host in ('example', 'invalid', 'localhost', 'test', ):
            self.top_level_domain = ''
            self.subdomains = ()
            self.domain = self.host
        else:
            self.top_level_domain, self.subdomains, self.domain = split_domains(self.host)

    @classmethod
    def from_string(cls, url):
        url.strip().lower()
        pass

    @property
    def url(self):
        url = ''
        if self.scheme != '':
            url += '{}://'.format(self.scheme)
        if self.username not in ('', None):
            if self.password not in ('', None):
                url += '{}:{}@'.format(self.username, self.password)
            else:
                url += '{}@'.format(self.username)
        url += self.host
        port_explicit_in_scheme = (self.scheme == 'http' and (self.port == 80 or self.port is None)) or \
                                  (self.scheme == 'https' and (self.port == 443 or self.port is None))
        if port_explicit_in_scheme:
            url += self.path
        elif self.port is not None:
            url += ':{}{}'.format(self.port, self.path)
        if self.query_string != '':
            url += '?{}'.format(self.query_string)
        if self.fragment != '':
            url += '#{}'.format(self.fragment)
        return url

    def __str__(self):
        return self.url

    def __repr__(self):
        return '{}({}, {}, {}, {}, {})'.format(
            self.__class__.__name__,
            repr(self.scheme),
            repr(self.host),
            repr(self.port),
            repr(self.path),
            repr(self.query_string),
        )

    def replace(self, **kwargs):
        url_kwargs = {
            'scheme': self.scheme, 'host': self.host, 'port': self.port, 'path': self.path, 
            'query_string': self.query_string, 'fragment': self.fragment,
        }
        url_kwargs.update(kwargs)
        return self.__class__(**url_kwargs)
