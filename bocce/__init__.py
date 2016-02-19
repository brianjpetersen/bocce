# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (surly, routing, )


__where__ = os.path.dirname(os.path.abspath(__file__))
__all__ = ('Application', 'application', 'Routes', 'routing', 'Request', 
           'Response', 'exceptions', 'surly', )


with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()
