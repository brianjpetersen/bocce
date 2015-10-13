# standard libraries
import os
# third party libraries
import webob
# first party libraries
from . import surly


__all__ = ('Request', '__where__')
__where__ = os.path.dirname(os.path.abspath(__file__))


class Request(webob.Request):

    _url = None
    
    @property
    def url(self):
        url = getattr(self, '_url', None)
        if url is None:
            url = surly.Url(
                scheme=self.scheme, host=self.domain, port=self.host_port, 
                path=self.path, query_string=self.query_string,
            )
        return url