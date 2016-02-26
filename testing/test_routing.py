# standard libraries
import datetime
# third party libraries
import pytest
# first party libraries
import bocce.routing as routing


@pytest.mark.parametrize(
    'route_path, match_path, segments',
    [
        (
            '', '/', {},
        ),
        (
            '/', '', {},
        ),
        (
            'a/b/c', 'a/b/c', {},
        ),
        (
            '{a}/b', 'a/b', {'a': 'a'},
        ),
        (
            '<a>/b', 'a/b', {'a': 'a'},
        ),
        (
            '<a>/d', 'a/b/c/d', {'a': 'a/b/c'},
        ),
        (
            '{a}/b/<c>', 'a/b/c/d', {'a': 'a', 'c': 'c/d'},
        ),
        (
            '{a}/b/<c>/', 'a/b/c/d/', {'a': 'a', 'c': 'c/d'},
        ),
        (
            '{a}/b/<c>', 'a/b/c/d/', {'a': 'a', 'c': 'c/d/'},
        ),
    ]
)
def test_route_match(route_path, match_path, segments):
    response = lambda request, configuration: None
    route = routing.Route(route_path, response)
    assert route.match(match_path) == segments


@pytest.mark.parametrize(
    'route_path, match_path',
    [
        (
            'a', ''
        ),
        (
            'a/{b}', '/b/c'
        ),
        (
            'a/<b>', '/b/c'
        ),
        (
            'a/<b>/', '/a/b'
        ),
    ]
)
def test_route_mismatch(route_path, match_path):
    response = lambda request, configuration: None
    route = routing.Route(route_path, response)
    assert route.match(match_path) is None


def test_route_match_with_methods_and_subdomains():
    response = lambda request, configuration: None
    route = routing.Route('{a}/b', response)
    assert route.match('a/b') == {'a': 'a'}
    assert route.match('a/b', method='POST') == None
    assert route.match('a/b', subdomain='api') == None
    route = routing.Route(
        '{a}/b', response, methods=('POST', ), subdomains=('api', 'www', )
    )
    assert route.match('a/b', method='POST', subdomain='api') == {'a': 'a'}


def test_route_match_with_methods():
    response = lambda request, configuration: None
    route = routing.Route('{a}/b', response)
    assert route.match('a/b') == {'a': 'a'}
    route = routing.Route('{a}/b', response, methods=('GET', 'POST', ))
    assert route.match('a/b') == None
    assert route.match('a/b', method='POST') == {'a': 'a'}


def test_route_match_with_subdomains():
    response = lambda request, configuration: None
    route = routing.Route('{a}/b', response)
    assert route.match('a/b') == {'a': 'a'}
    route = routing.Route('{a}/b', response, subdomains=('www', 'api', ))
    assert route.match('a/b') == None
    assert route.match('a/b', subdomain='api') == {'a': 'a'}


def test_routes_container():
    routes = routing.Routes()
    assert len(routes) == 0
    response = lambda request, configuration: None
    routes.add_response('/', response)
    routes.add_response('/a', response)
    assert len(routes) == 2
    routes.pop()
    assert len(routes) == 1
    route = routing.Route('/a', response)
    routes.extend((route, route, ))
    assert len(routes) == 3
    assert routes[-1] == route


routes = routing.Routes()
response = lambda request, response: None
routes.add_response('', response)
routes.add_response('a', response, methods=('GET', 'POST', ))
routes.add_response('{a}/b', response, methods=('GET', 'POST', ))
routes.add_response('{a}/c', response)
routes.add_response('{a}/<b>', response)
routes.add_response('{a}/b/<c>', response)
routes.add_response('{a}/a/{c}/<d>', response)

@pytest.mark.parametrize(
    'path, method, route, segments',
    [
        (
            '', None, routes[0], {}
        ),
        (
            '/', None, routes[0], {}
        ),
        (
            'a', 'GET', routes[1], {}
        ),
        (
            'a/c', 'GET', routes[3], {'a': 'a'}
        ),
        (
            'a/b', 'GET', routes[2], {'a': 'a'}
        ),
        (
            'a/d', 'GET', routes[4], {'a': 'a', 'b': 'd'}
        ),
        (
            '/a/d', 'GET', routes[4], {'a': 'a', 'b': 'd'}
        ),
        (
            '/a/d/', None, routes[4], {'a': 'a', 'b': 'd/'}
        ),
        (
            'a/b/c', None, routes[5], {'a': 'a', 'c': 'c'}
        ),
        (
            'a/b/c/d/', None, routes[5], {'a': 'a', 'c': 'c/d/'}
        ),
        (
            'a/a/b/c/d/', None, routes[6], {'c': 'b', 'a': 'a', 'd': 'c/d/'}
        ),
    ]
)
def test_routes_matching(path, method, route, segments):
    assert routes.match(path, method) == (route, segments)


def test_routes_benchmark(N=1000):
    routes.cache.size = 0
    start = datetime.datetime.now()
    for i in range(N):
        routes.match('a/a/b/c/d/')
    stop = datetime.datetime.now()
    duration = (stop - start).total_seconds()/float(N)
    assert duration < 1e-4


if __name__ == '__main__':
    pytest.main()
