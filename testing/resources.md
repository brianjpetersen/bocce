```python
>>> import bocce

```

# Initialization

```python
>>> resource = bocce.Resource('request', 'response', 'match')
>>> resource.request, resource.response, resource.match
('request', 'response', 'match')
>>> class MyResource(bocce.Resource):
...     def __init__(self):
...         self.my_attribute = 'my_attribute'
>>> resource = MyResource('request', 'response', 'match')
>>> resource.request, resource.response, resource.match
('request', 'response', 'match')
>>> resource.my_attribute
'my_attribute'

```

