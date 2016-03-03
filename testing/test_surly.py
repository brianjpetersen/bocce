# standard libraries
pass
# third party libraries
import pytest
# first party libraries
import bocce.surly as surly


@pytest.mark.parametrize(
    'host, host_components',
    [
        (
            'a.b.com',
            (('a', ), 'b', 'com')
        ),
        (
            'a.b.net',
            (('a', ), 'b', 'net')
        ),
        (
            'a.b.gov',
            (('a', ), 'b', 'gov')
        ),
        (
            'a.b.org',
            (('a', ), 'b', 'org')
        ),
        (
            'a.b.org',
            (('a', ), 'b', 'org')
        ),
        (
            'a.b.c.org',
            (('a', 'b', ), 'c', 'org')
        ),
        (
            'a.b.c.d',
            (('a', 'b', 'c', ), 'd', None)
        ),
        (
            '',
            (None, None, None)
        ),
    ]
)
def test_split_http_host(host, host_components):
    assert surly.split_host(host) == host_components


def construct_url_dict(**components):
    url_dict = {
        'scheme': None, 
        'user': None, 
        'password': None, 
        'host': None,
        'port': None,
        'path': None, 
        'query_string': None, 
        'fragment': None, 
    }.copy()
    url_dict.update(components)
    return url_dict

@pytest.mark.parametrize(
    'input, expected',
    [
        (
            'http://localhost:8080',
            construct_url_dict(scheme='http', host='localhost', port='8080')
        ),
        (
            'http://localhost',
            construct_url_dict(scheme='http', host='localhost')
        ),
        (
            'localhost',
            construct_url_dict(host='localhost')
        ),
        (
            'localhost:8080',
            construct_url_dict(host='localhost', port='8080')
        ),
        (
            'http://localhost/a/b',
            construct_url_dict(scheme='http', host='localhost', path='a/b')
        ),
        (
            'https://username:password@localhost:443/a/b?test=3#frag',
            construct_url_dict(
                scheme='https', user='username', password='password',
                host='localhost', port='443', path='a/b', query_string='test=3',
                fragment='frag',
            )
        ),
    ]
)
def test_split_url(input, expected):
    assert surly.split_url(input) == expected


@pytest.mark.parametrize(
    'input, expected',
    [
        (
            {
                'scheme': 'http', 'host': 'localhost', 'port': '8080'
            },
            'http://localhost:8080'
        ),
        (
            {
                'scheme': 'https', 'user': 'username', 'password': 'password',
                'host': 'localhost', 'port': '443', 'path': 'a/b', 
                'query_string': 'test=3', 'fragment': 'frag'
            },
            'https://username:password@localhost:443/a/b?test=3#frag'
        ),
        (
            {
                'scheme': 'https', 'user': 'username', 'password': 'p@$$word!',
                'host': 'localhost', 'port': '443', 'path': 'a/b', 
                'query_string': 'test=3', 'fragment': 'frag'
            },
            'https://username:p@$$word!@localhost:443/a/b?test=3#frag'
        ),
        (
            {
                'scheme': 'https', 'user': 'username', 'password': 'p@$$word!',
                'host': 'localhost', 'port': '443', 'path': 'a/b', 
                'query_string': 'test=3', 'fragment': 'frag', 'quote': True,
            },
            'https://username:p%40%24%24word%21@localhost:443/a/b?test=3#frag'
        ),
    ]
)
def test_construct_url(input, expected):
    assert surly.construct_url(**input) == expected


class TestQueryString:
    
    def test_str(self):
        query_string = surly.QueryString.from_string('a=1&b=2&c=3')
        assert str(query_string) == 'a=1&b=2&c=3'

    def test_repr(self):
        query_string = surly.QueryString.from_string('a=1&b=2&c=3')
        assert repr(query_string) == \
               "bocce.surly.QueryString(('a', '1'), ('b', '2'), ('c', '3'))"

    def test_get_singleton(self):
        query_string = surly.QueryString.from_string('a=1&b=2&c=3')
        assert query_string['a'] == '1'
        
    def test_get_multiple(self):
        query_string = surly.QueryString.from_string('a=1&b=2&a=2')
        assert query_string['a'] == ['1', '2']
        
    def test_get_first(self):
        query_string = surly.QueryString.from_string('a=1&b=2&a=2')
        assert query_string.get_first('a') == '1'
        
    def test_get_last(self):
        query_string = surly.QueryString.from_string('a=1&b=2&a=2')
        assert query_string.get_last('a') == '2'
        
    def test_separator(self):
        query_string = surly.QueryString.from_string(
            'a=1&b=2;c=3', separator=';'
        )
        assert str(query_string) == 'a=1;b=2;c=3'
    
    def test_from_dict(self):
        query_string_dict_items = [('a', 1), ('b', 2)]
        query_string = surly.QueryString(query_string_dict_items)
        assert str(query_string) == 'a=1&b=2'
        
    def test_without_pair(self):
        query_string = surly.QueryString.from_string('a&b=2;c=3')
        assert str(query_string) == 'a&b=2&c=3'


class TestUrl:
    
    def test_url_localhost(self):
        url = surly.Url.from_string('localhost')
        assert url.path is None
        assert url.scheme is None
    
    def test_url_from_string(self):
        url = 'https://username:password@localhost:443/a/b?test=3#frag'
        assert str(surly.Url.from_string(url)) == url
        
    def test_repr(self):
        url = 'http://localhost/a'
        assert repr(surly.Url.from_string(url)) == \
            "Url('localhost', 'a', 'http', None, None, None, None, None, False)"
               
    def test_url_replace(self):
        url = surly.Url(scheme='http', host='localhost', path='a/b')
        assert 'http://localhost:8080/a/b/c' == str(url.replace(
            port=8080, path='a/b/c'
        ))
        
    def test_url_attrs(self):
        url = surly.Url.from_string(
            'https://username:password@localhost:443/a/b?test=3#frag'
        )
        assert url.scheme == 'https'
        assert url.user == 'username'
        assert url.password == 'password'
        assert url.host == 'localhost'
        assert url.port == 443
        assert url.path == 'a/b'
        assert str(url.query_string) == 'test=3'
        assert url.fragment == 'frag'


if __name__ == '__main__':
    pytest.main()
