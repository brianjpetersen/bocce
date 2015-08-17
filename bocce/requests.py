# standard libraries
import os
# third party libraries
import webob
# first party libraries
pass


__all__ = ('Request', '__where__')
__where__ = os.path.dirname(os.path.abspath(__file__))


class Request(webob.Request):

    pass