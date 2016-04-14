# standard libraries
import json
# third party libraries
pass
# first party libraries
import bocce


def application(environment, start_response):
    request = bocce.Request.from_environment(environment)
    response = bocce.Response()
    response.headers['age'] = 305
    response.cookies['a'] = 1
    response.cookies['b'] = 2
    response.body.json = {'a': 1, 'b': 5*'2'}
    #response.body.file = 'scratch.py'
    response.body.compress()
    return response.start(start_response)


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 8080, application)
