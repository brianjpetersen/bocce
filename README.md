# bocce

Bocce is a fast, un-opinionated, Pythonic, no-nonsense WSGI microframework.  It is MIT-licensed.

## Features

* Carefully-crafted Pythonic API.  Don't believe it?
  * What other framework provides per-request setup/teardown functionality through a context manager?
  * What other framework allows you to define routes with a dict API?
* Explicit is better than implicit.  No magic thread/context local state variables.  No circular import references necessitated by a global app variable.
* Flexible URL dispatch with *fast* tree-based matching (no impenetrable regexes!) and configurable route caching.
* Easy to extend.  Bocce is 100% Python and was designed for object-oriented extensibility through inheritence and mixins.
* Easy to scale.  Easily merge the routes and configuration from one application to another.  You want multiple apps?  You've got multiple apps.
* Respectful of REST and WSGI.  Design and nomenclature that reflects ideals of Fielding and PEP333.
* Configuration defined on an application-level and managed per resource prior to serving.
* No templating engine.  No database ORM.  No auth hooks.  No nonsense.  You know what should be in your stack much better than some framework designer.  Take control.
* Lightweight.  You can review the source in less than 20 minutes, and its only dependency is webob (and, optionally, waitress as a development server).


## Examples

