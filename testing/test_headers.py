# standard libraries
import datetime
# third party libraries
import pytest
# first party libraries
import bocce


response = bocce.Response()

#response.body.json['a'] = 1
#response.body.json['b'] = datetime.datetime.now()

response.body.html = '<html></html>'

response.cookies.set('a', 1, http_only=True)

print(list(response.headers))
print(list(response.body))


"""
from bocce.headers import (RequestHeaders, ResponseHeaders, )
from bocce.cookies import (ResponseCookies, ResponseCookie, )


class TestRequestHeaders:
    
    headers = RequestHeaders(
        ('accept-encoding', 'gzip'),
        ('Accept-Encoding', 'deflate'),
        ('Accept-Language', 'en-US,en;q=0.8'),
    )
    
    def test_cookies(self):
        headers = RequestHeaders(('Cookie', 'a=0; b=2; c=3; a=1;'))
        assert headers.cookies['a'] == '1'
        assert len(headers.cookies) == 3
    
    def test_from_environment(self):
        headers = RequestHeaders.from_environment({
            'CONTENT_LENGTH': 10,
            'CONTENT_TYPE': 'application/json',
            'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.8',
        })
        assert headers['content-length'] == '10'
        assert headers['content-type'] == 'application/json'
        assert headers['accept-language'] == 'en-US,en;q=0.8'
    
    def test_contains(self):
        assert ('accept-encoding' in self.headers) == True
        assert ('ACCEPT-ENCODING' in self.headers) == True
        assert ('asdf' in self.headers) == False
    
    def test_get(self):
        assert self.headers['accept-language'] == 'en-US,en;q=0.8'
        assert self.headers['accept-encoding'] == ['gzip', 'deflate']
        assert self.headers['Accept-Encoding'] == ['gzip', 'deflate']
        assert self.headers.get('Accept-Encoding') == ['gzip', 'deflate']
        assert self.headers.get_first('Accept-Encoding') == 'gzip'
        assert self.headers.get_last('Accept-Encoding') == 'deflate'
        with pytest.raises(KeyError):
            self.headers['Cookie']
        assert self.headers.get('Cookie') == None
    
    def test_len(self):
        assert len(self.headers) == 3
    
    def test_repr(self):
        assert repr(self.headers) == ("bocce.headers.RequestHeaders("
            "('Accept-Encoding', 'gzip'), ('Accept-Encoding', 'deflate'), "
            "('Accept-Language', 'en-US,en;q=0.8'))")
    
    def test_str(self):
        assert str(self.headers) == ('Accept-Encoding: gzip\n'
            'Accept-Encoding: deflate\n'
            'Accept-Language: en-US,en;q=0.8')


class TestResponseCookies:

    cookies = ResponseCookies()
    cookies['a'] = 0
    cookies['c'] = ResponseCookie('c', 3)
    cookies.set('b', 2, path='/b')

    def test_get_set(self):
        assert self.cookies['a'].key == 'a'
        assert self.cookies['a'].value == 0
        assert self.cookies['b'].value == 2
        assert self.cookies['b'].path == '/b'
        assert self.cookies['c'].value == 3
        
    def test_headers(self):
        assert self.cookies.headers == [
            ('Set-Cookie', 'a=0'),
            ('Set-Cookie', 'c=3'),
            ('Set-Cookie', 'b=2; Path=/b'),
        ]
        
    def test_values(self):
        assert [str(value) for value in self.cookies.values()] == [
            'a=0', 'c=3', 'b=2; Path=/b',
        ]
        

class TestResponseHeaders:
    
    def test_get(self):
        headers = ResponseHeaders(
            ('age', 60),
            ('Cache-Control', 'no-cache'),
        )
        assert headers['age'] == '60'
        
    def test_len(self):
        headers = ResponseHeaders(
            ('Age', 60),
            ('Cache-Control', 'no-cache'),
        )
        assert len(headers) == 2
        
    def test_set(self):
        headers = ResponseHeaders()
        headers['age'] = 60
        assert headers['age'] == '60'
        headers['age'] = 30
        assert headers['age'] == ['60', '30']
        
    def test_delete(self):
        headers = ResponseHeaders()
        headers['age'] = 60
        headers['age'] = 30
        headers.delete('age')
        headers['age'] = 45
        assert headers['age'] == '45'
        
    def test_contains(self):
        headers = ResponseHeaders()
        headers['Age'] = 60
        assert 'age' in headers
    
    def test_cookies(self):
        headers = ResponseHeaders()
        assert list(headers) == []
        assert ('set-cookie' in headers) == False
        headers.cookies['a'] = 0
        assert ('set-cookie' in headers) == True
        assert list(headers) == [('Set-Cookie', 'a=0')]
        headers['age'] = 60
        assert headers['Age'] == '60'
        assert list(headers) == [('Age', '60'), ('Set-Cookie', 'a=0'), ]
        headers['cache'] = 'no-store'
        headers['cache'] = 'no-cache'
        headers.cookies.set('b', 1, path='/b')
        assert list(headers) == [
            ('Age', '60'),
            ('Cache', 'no-store'),
            ('Cache', 'no-cache'),
            ('Set-Cookie', 'a=0'),
            ('Set-Cookie', 'b=1; Path=/b'),
        ]


if __name__ == '__main__':
    pytest.main()
"""