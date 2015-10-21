```python
>>> import bocce

```

# Initialization

```python
>>> bocce.Routes == bocce.routing.Routes
True
>>> routes = bocce.Routes()
>>> routes.cache.size == 1e6
True
>>> routes = bocce.Routes(cache=None)
>>> routes.cache is None
True
>>> routes = bocce.Routes(cache=-1)
Traceback (most recent call last):
 ...
ValueError

```

# Sequence Attributes and Methods

```python
>>> routes = bocce.Routes()
>>> routes['/'] = '/'
>>> routes['/a/b'] = '/a/b'
>>> routes['/a/b/'] = '/a/b'
>>> routes['c'] = 'c'
>>> list(routes)
['/', '/a/b', '/a/b/', '/c']
>>> len(routes)
4
>>> routes['c'] = 'duplicate'
>>> len(routes)
4
>>> routes['/']
'/'
>>> routes['']
'/'
>>> routes['/a/b']
'/a/b'
>>> routes['c']
'duplicate'
>>> list(routes)
['/', '/a/b', '/a/b/', '/c']
>>> routes['/d']
Traceback (most recent call last):
 ...
RouteKeyError
>>> del routes['/a']
Traceback (most recent call last):
 ...
RouteKeyError
>>> del routes['/a/b']
>>> routes['/a/b']
Traceback (most recent call last):
 ...
RouteKeyError
>>> len(routes)
3
>>> list(routes)
['/', '/a/b/', '/c']

```

# Cache

```python
>>> routes = bocce.Routes()
>>> routes['/a/{b}/c'] = '/a/{b}/c'
>>> match = routes.match('/a/b/c')
>>> match.resource
'/a/{b}/c'
>>> match.segments
{'b': 'b'}
>>> match = routes.match('/a/b/c')
>>> match.resource
'/a/{b}/c'
>>> match.segments
{'b': 'b'}

```

# Equivalent Paths

```python
>>> routes = bocce.Routes()
>>> routes['/{a}'] = 'a'
>>> routes['/{b}'] = 'b'
>>> list(routes)
['/{b}']
>>> routes['/{b}']
'b'
>>> routes['/<c>'] = 'c'
>>> routes['/<d>'] = 'd'
>>> list(routes)
['/{b}', '/<d>']

>>> routes = bocce.Routes(raise_on_duplicate=True)
>>> routes['/{a}'] = 'a'
>>> routes['/{b}'] = 'b'
Traceback (most recent call last):
 ...
RouteDuplicateError

```

# Sorting Paths

```python
>>> routes = bocce.Routes()
>>> routes[''] = None
>>> routes['/a'] = None
>>> routes['/c'] = None
>>> routes['/c/'] = None
>>> routes['/a/'] = None
>>> routes['/a/b'] = None
>>> routes['/a/b/'] = None
>>> routes['a/{b}'] = None
>>> routes['a/{b}/'] = None
>>> routes['a/<b>'] = None
>>> routes['a/<b>/'] = None
>>> for path in routes:
...     print(repr(path))
'/'
'/a'
'/a/'
'/a/b'
'/a/b/'
'/a/{b}'
'/a/{b}/'
'/a/<b>'
'/a/<b>/'
'/c'
'/c/'

```

# Matching Paths

```python
>>> routes = bocce.Routes()
>>> routes[''] = ''
>>> match = routes.match('')
>>> match.resource
''
>>> match = routes.match('/')
>>> match.resource
''

>>> routes = bocce.Routes()
>>> routes['a/'] = 'a/'
>>> match = routes.match('a/')
>>> match.resource
'a/'
>>> match = routes.match('a')
>>> isinstance(match, bocce.routing.Detour)
True
>>> match.resource is None
True

>>> routes = bocce.Routes()
>>> routes['<a>'] = '<a>'
>>> match = routes.match('')
>>> match.resource
'<a>'
>>> match = routes.match('a')
>>> match.resource
'<a>'
>>> match.segments
{'a': ['a']}
>>> match = routes.match('a/b/c')
>>> match.segments
{'a': ['a', 'b', 'c']}

>>> routes = bocce.Routes()
>>> routes['a/{b}'] = 'a/{b}'
>>> routes['{a}/{b}'] = '{a}/{b}'
>>> routes['<a>'] = '<a>'
>>> match = routes.match('a/b')
>>> match.resource
'a/{b}'
>>> match.segments
{'b': 'b'}
>>> match = routes.match('b/c')
>>> match.resource
'{a}/{b}'
>>> match.segments
{'a': 'b', 'b': 'c'}
>>> match = routes.match('a/b/c')
>>> match.resource
'<a>'
>>> match.segments
{'a': ['a', 'b', 'c']}

>>> routes = bocce.Routes()
>>> routes['{a}/b'] = '{a}/b'
>>> routes['a/{b}'] = 'a/{b}'
>>> match = routes.match('a/b')
>>> match.resource
'a/{b}'
>>> match.segments
{'b': 'b'}
>>> match = routes.match('b/b')
>>> match.resource
'{a}/b'
>>> match.segments
{'a': 'b'}

>>> routes = bocce.Routes()
>>> routes['a'] = 'a'
>>> routes['<a>'] = '<a>'
>>> routes['<a>/2/z'] = '<a>/2/z'
>>> routes['<a>/2/<z>'] = '<a>/2/<z>'
>>> match = routes.match('/')
>>> match.resource
'<a>'
>>> match = routes.match('a')
>>> match.resource
'a'
>>> match = routes.match('a/b')
>>> match.resource
'<a>'
>>> match.segments
{'a': ['a', 'b']}
>>> match = routes.match('a/b/2/z')
>>> match.resource
'<a>/2/z'
>>> match.segments
{'a': ['a', 'b']}
>>> match = routes.match('a/b/2/y/z')
>>> match.resource
'<a>/2/<z>'
>>> match.segments
{'a': ['a', 'b'], 'z': ['y', 'z']}
>>> match = routes.match('a/b/.../y/z')
>>> match.resource
'<a>'
>>> match.segments
{'a': ['a', 'b', '...', 'y', 'z']}

```

# Mounting Routes

```python
>>> routes_1 = bocce.Routes()
>>> routes_1['/'] = 'routes_1: /'
>>> routes_1['/a'] = 'routes_1: /a'
>>> routes_1['/b'] = 'routes_1: /b'
>>> routes_1['/a/b'] = 'routes_1: /a/b'
>>> routes_2 = bocce.Routes()
>>> routes_2['/'] = 'routes_2: /'
>>> routes_2['/a'] = 'routes_2: /a'
>>> routes_2['/b'] = 'routes_2: /b'
>>> routes_2['/a/b'] = 'routes_2: /a/b'
>>> routes_2['/c/'] = 'routes_2: /c/'
>>> routes_2['c'] = 'routes_2: c'

>>> routes = bocce.Routes()
>>> routes['/routes_1'] = routes_1
>>> routes['/routes_2'] = routes_2
>>> for path in routes:
...     print(path, routes[path])
('/routes_1', 'routes_1: /')
('/routes_1/a', 'routes_1: /a')
('/routes_1/a/b', 'routes_1: /a/b')
('/routes_1/b', 'routes_1: /b')
('/routes_2', 'routes_2: /')
('/routes_2/a', 'routes_2: /a')
('/routes_2/a/b', 'routes_2: /a/b')
('/routes_2/b', 'routes_2: /b')
('/routes_2/c', 'routes_2: c')
('/routes_2/c/', 'routes_2: /c/')

>>> routes = bocce.Routes()
>>> routes[''] = routes_2
>>> for path in routes:
...     print(path, routes[path])
('/', 'routes_2: /')
('/a', 'routes_2: /a')
('/a/b', 'routes_2: /a/b')
('/b', 'routes_2: /b')
('/c', 'routes_2: c')
('/c/', 'routes_2: /c/')
>>> routes['/'] = routes_1
>>> for path in routes:
...     print(path, routes[path])
('/', 'routes_1: /')
('/a', 'routes_1: /a')
('/a/b', 'routes_1: /a/b')
('/b', 'routes_1: /b')
('/c', 'routes_2: c')
('/c/', 'routes_2: /c/')
  
>>> routes = bocce.Routes()
>>> routes_1 = bocce.Routes()
>>> routes_1['/'] = 'routes_1: /'
>>> routes_1['/{a}'] = 'routes_1: /{a}'
>>> routes_1['/{a}/b'] = 'routes_1: /{a}/b'
>>> routes_1['/<c>'] = 'routes_1: /<c>'
>>> routes['/'] = routes_1
>>> for path in routes:
...     print(path, routes[path])
('/', 'routes_1: /')
('/{a}', 'routes_1: /{a}')
('/{a}/b', 'routes_1: /{a}/b')
('/<c>', 'routes_1: /<c>')

```