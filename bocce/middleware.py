# standard libraries
import os
# third party libraries
pass
# first party libraries
pass


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
