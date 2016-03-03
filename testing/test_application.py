# standard libraries
import json
# third party libraries
pass
# first party libraries
import bocce


def application(environment, start_response):
    request = bocce.Request.from_environment(environment)
    print(repr(request.cookies))
    """
    if request.body.content:
        print(request.body, request.url, request.http)
        print(request.body.json)
    """
    response = bocce.Response()
    response.set_cookie('a', 'b')
    response.set_cookie('b', 'c')
    #print(type(response.headers))
    #print(response.headers['Set-Cookie'])
    return response(environment, start_response)
    

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 8080, application)
