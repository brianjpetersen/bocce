# standard libraries
import os
import doctest
# third party libraries
pass
# first party libraries
import bocce


doctest.testfile('routing.md', optionflags=doctest.ELLIPSIS)
doctest.testfile('application.md', optionflags=doctest.ELLIPSIS)
doctest.testmod(bocce.surly)