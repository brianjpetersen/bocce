# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (exceptions, )


__where__ = os.path.dirname(os.path.abspath(__file__))


def compress(request, response, configuration):
    defaults = {'level': 2, 'threshold': 128, }
    configuration = configuration.get('bocce', {}).get('compression', defaults)
    if 'gzip' in request.accept.encodings:
        try:
            response.body.compress(
                configuration['level'],
                configuration['threshold']
            )
        except:
            pass


def require_https(request, response, configuration):
    secure = configuration.get('bocce', {}).get('secure', True)
    if secure == False:
        return
    if request.url.scheme != 'https':
        response = exceptions.PermanentRedirectHandler(scheme='https', port=None)
        raise response
    # require https for all future requests on this domain
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
