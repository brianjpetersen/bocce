```python
>>> import bocce
>>> debug = False

``` 

# Define Resources

```python
>>> class GreetingResource(bocce.Resource):
...     
...     @classmethod
...     def configure(cls, configuration):
...         cls.corny_names = configuration['corny_names']
...     
...     def __call__(self, name, salutation):
...         if name in self.corny_names:
...             response = bocce.exceptions.Response()
...             response.status = '400 Bad Request'
...             response.body = 'I find your lack of originality disturbing.'
...             raise response
...         if self.request.method != 'GET':
...             response = bocce.exceptions.Response()
...             response.status = '405 Method Not Allowed'
...             raise response
...         response = bocce.Response()
...         if name == '':
...             response.body = '{}!'.format(salutation)
...         else:
...             response.body = '{}, {}!'.format(salutation, name)
...         response.status = '200 OK'
...         return response
...     
...     def __enter__(self):
...         name = self.route.segments.get('name', '')
...         salutation = self.request.params.get('salutation', 'Hello')
...         return self, {'name': name, 'salutation': salutation}

>>> class ExceptionResource(bocce.Resource):
...     
...     def __call__(self):
...         raise Exception()

```

# Setup Application and Routes


```python
>>> application = bocce.Application()
>>> application.routes['/greetings'] = GreetingResource
>>> application.routes['/greetings/{name}'] = GreetingResource
>>> application.routes['/whoops'] = ExceptionResource
>>> application.configuration['corny_names'] = set(('World', ))
>>> application.configure()
>>> if debug:
...     import logging, sys
...     handler = logging.StreamHandler(stream=sys.stderr)
...     application.logger.addHandler(handler)

```

# Handle Requests

```python

>>> request = bocce.Request.blank('/greetings')
>>> response = request.get_response(application)
>>> print(response)
200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 6
<BLANKLINE>
Hello!

>>> request = bocce.Request.blank('/greetings/Tim')
>>> response = request.get_response(application)
>>> print(response)
200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 11
<BLANKLINE>
Hello, Tim!

>>> request = bocce.Request.blank('/greetings/Guido?salutation=Hallo')
>>> response = request.get_response(application)
>>> print(response)
200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 13
<BLANKLINE>
Hallo, Guido!

>>> request = bocce.Request.blank('/farewells')
>>> response = request.get_response(application)
>>> print(response)
404 Not Found
Content-Type: text/html; charset=UTF-8
Content-Length: 0

>>> request = bocce.Request.blank('/greetings', method='POST')
>>> response = request.get_response(application)
>>> print(response)
405 Method Not Allowed
Content-Type: text/html; charset=UTF-8
Content-Length: 0

>>> request = bocce.Request.blank('/greetings/World')
>>> response = request.get_response(application)
>>> print(response)
400 Bad Request
Content-Type: text/html; charset=UTF-8
Content-Length: 43
<BLANKLINE>
I find your lack of originality disturbing.

>>> request = bocce.Request.blank('/whoops')
>>> response = request.get_response(application)
>>> print(response)
500 Internal Server Error
Content-Type: text/html; charset=UTF-8
Content-Length: 0

>>> application.server_error_resource = bocce.exceptions.DebugServerErrorResource
>>> request = bocce.Request.blank('/whoops')
>>> response = request.get_response(application)
>>> print(response)
500 Internal Server Error
Content-Type: text/html; charset=UTF-8
Content-Length: 258
<BLANKLINE>
Traceback (most recent call last):
...
Exception
<BLANKLINE>

```