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

# Sequence

```python
>>> routes = bocce.Routes()
>>> routes['/'] = 'root starting with slash'
>>> routes[''] = 'root starting without slash'
>>> routes['/a/b'] = 'two segments starting with slash'
>>> routes['/a/b/'] = 'two segments starting and ending with slash'
>>> routes['duplicate'] = 'first'
>>> list(routes)
['', 'duplicate', '/', '/a/b', '/a/b/']
>>> len(routes)
5
>>> routes['duplicate'] = 'second'
>>> len(routes)
5
>>> routes['/']
'root starting with slash'
>>> routes['']
'root starting without slash'
>>> routes['/a/b']
'two segments starting with slash'
>>> routes['duplicate']
'second'
>>> list(routes)
['', 'duplicate', '/', '/a/b', '/a/b/']
>>> routes['/segment_1']
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
4
>>> list(routes)
['', 'duplicate', '/', '/a/b/']

```

# Equivalence

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

```

# Sorting

```python
>>> routes = bocce.Routes()
>>> routes['/'] = None
>>> routes['/a'] = None
>>> routes['/c'] = None
>>> routes['/c/'] = None
>>> routes['/a/'] = None
>>> routes['/a/b'] = None
>>> routes['/a/b/'] = None
>>> routes[''] = None
>>> routes['a'] = None
>>> routes['b/'] = None
>>> routes['a/b'] = None
>>> routes['a/b/'] = None
>>> routes['a/{b}/'] = None
>>> routes['a/<b>/'] = None
>>> for path in routes:
...     print(repr(path))
''
'a'
'a/b'
'a/b/'
'a/{b}/'
'a/<b>/'
'b/'
'/'
'/a'
'/a/'
'/a/b'
'/a/b/'
'/c'
'/c/'

```

# Matching

```python
>>> routes = bocce.Routes()
>>> routes[''] = ''
>>> match = routes.match('')
>>> match.handler
''
>>> match = routes.match('/')
>>> isinstance(match, bocce.routing.Mismatch)
True
>>> match.handler is None
True

>>> routes = bocce.Routes()
>>> routes['a/'] = 'a/'
>>> match = routes.match('a/')
>>> match.handler
'a/'
>>> match = routes.match('a')
>>> isinstance(match, bocce.routing.Mismatch)
True
>>> match.handler is None
True

>>> routes = bocce.Routes()
>>> routes['<a>'] = '<a>'
>>> match = routes.match('')
>>> match.handler
'<a>'
>>> match = routes.match('a')
>>> match.handler
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
>>> match.handler
'a/{b}'
>>> match.segments
{'b': 'b'}
>>> match = routes.match('b/c')
>>> match.handler
'{a}/{b}'
>>> match.segments
{'a': 'b', 'b': 'c'}
>>> match = routes.match('a/b/c')
>>> match.handler
'<a>'
>>> match.segments
{'a': ['a', 'b', 'c']}

>>> routes = bocce.Routes()
>>> routes['{a}/b'] = '{a}/b'
>>> routes['a/{b}'] = 'a/{b}'
>>> match = routes.match('a/b')
>>> match.handler
'a/{b}'
>>> match.segments
{'b': 'b'}
>>> match = routes.match('b/b')
>>> match.handler
'{a}/b'
>>> match.segments
{'a': 'b'}

>>> routes = bocce.Routes()
>>> routes['a'] = 'a'
>>> routes['<a>'] = '<a>'
>>> routes['<a>/2/z'] = '<a>/2/z'
>>> routes['<a>/2/<z>'] = '<a>/2/<z>'
>>> match = routes.match('/')
>>> isinstance(match, bocce.routing.Mismatch)
True
>>> match = routes.match('a')
>>> match.handler
'a'
>>> match = routes.match('a/b')
>>> match.handler
'<a>'
>>> match.segments
{'a': ['a', 'b']}
>>> match = routes.match('a/b/2/z')
>>> match.handler
'<a>/2/z'
>>> match.segments
{'a': ['a', 'b']}
>>> match = routes.match('a/b/2/y/z')
>>> match.handler
'<a>/2/<z>'
>>> match.segments
{'a': ['a', 'b'], 'z': ['y', 'z']}
>>> match = routes.match('a/b/.../y/z')
>>> match.handler
'<a>'
>>> match.segments
{'a': ['a', 'b', '...', 'y', 'z']}


```