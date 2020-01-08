# standard libraries
import datetime
import random
# third party libraries
pass
# first party libraries
import bocce


def sample_with_replacement(population, N):
    i = 0
    while i < N:
        yield random.choice(population)
        i += 1


def benchmark(cache, matches=1e5):
    # construct paths to match
    paths = 50*('/', ) + \
                 2*('/api', ) + \
                 1*('/api/1.1', ) + \
                25*('/api/1.1/users', ) + \
                 2*('/api/1.1/users/guido', ) + \
                10*('/api/health', ) + \
                 3*('/api/1.1/users/guido/education', ) + \
                 3*('/api/1.1/users/guido/parents', ) + \
                 1*('/api/1.1/users/guido/children', ) + \
                 1*('/api/users', )
    paths = list(sample_with_replacement(paths, matches))

    # setup routes
    routes = bocce.Routes(cache)
    routes['/'] = '/'
    routes['/api'] = '/api'
    routes['/api/{version}'] = '/api/{version}'
    routes['/api/{version}/users'] = '/api/{version}/users'
    routes['/api/{version}/users/{username}'] = '/api/{version}/users'
    routes['/api/health'] = '/api/health'
    routes['/api/{version}/users/{username}/education'] = '/api/{version}/users/{username}/education'
    routes['/api/{version}/users/{username}/parents'] = '/api/{version}/users/{username}/parents'
    routes['/api/{version}/users/{username}/children'] = '/api/{version}/users/{username}/children'
    routes['/api/{version}/users/{username}/friends'] = '/api/{version}/users/{username}/friends'

    # evaluate performance
    when_started = datetime.datetime.utcnow()
    for path in paths:
        match = routes.match(path)
    when_ended = datetime.datetime.utcnow()

    duration = (when_ended - when_started).total_seconds()
    duration_per_match = duration/float(matches)

    return duration_per_match


if __name__ == '__main__':
    print('With caching: {} usec'.format(1e6*benchmark(cache=1e5)))
    print('Without caching: {} usec'.format(1e6*benchmark(cache=None)))
