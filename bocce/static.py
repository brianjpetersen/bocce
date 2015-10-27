# standard libraries
import os
import mimetypes
import zlib
import posixpath
# third party libraries
pass
# first party libraries
from . import (responses, resources, exceptions, )


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


_directory_template = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
  <head>
    <title>Directory Listing for {full_url_path}</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css">
    <link href='http://fonts.googleapis.com/css?family=Lato&subset=latin,latin-ext' rel='stylesheet' type='text/css'>
    <style type="text/css">
        body{{background-color: #f1f1f1; font-family: Lato;}}
    </style>
  </head>
  <body>
    <h1>Directory Listing for {full_url_path}</h1>
    <hr>
    <ul class="fa-ul">
      {directory_list}
    </ul>
    <hr>
  </body>
</html>'''


_directory_list_item_template = '''<li>
    {icon}<a href="{path}">{path}</a>
</li>'''


def _render_directory_list_item(path, is_file):
    if is_file:
        icon = '<i class="fa-li fa fa-file"></i>'
    else:
        if path.endswith('/') == False:
            path = path + '/'
        icon = '<i class="fa-li fa fa-folder"></i>'
    return _directory_list_item_template.format(path=path, icon=icon)


def _render_directory_template(url_path, os_path, full_url_path):
    items = [(os.path.isfile(os.path.join(os_path, path)), path) for path in os.listdir(os_path) if 
             path.startswith('.') == False]
    items.sort()
    directory_list = '\n'.join(_render_directory_list_item(path, is_file) for is_file, path in items)
    return _directory_template.format(
        url_path=url_path,
        directory_list=directory_list,
        full_url_path=full_url_path,
    )


def Resource(path, expose_directories=False, cache_zipped_files=True, prezip_files=False):
    
    class Resource(resources.Resource):
        
        @classmethod
        def configure(cls, configuration):
            super(Resource, cls).configure(configuration)

        def __init__(self, request, route):
            super(Resource, self).__init__(request, route)
            self.response = responses.Response()

        @property
        def method_not_allowed_response(self):
            response = exceptions.Response()

        def compress(self, minimum_size=999, level=2):
            #self.response.encode_content()
            return
            should_be_compressed = (
                'gzip' in self.request.accept_encoding and \
                len(self.response.body) > minimum_size
            )
            if should_be_compressed:
                self.response.body = zlib.compress(self.response.body, level)
                self.response.content_encoding = 'gzip'

        def __enter__(self):
            return self, {'url_path': '/'.join(self.route.matches.get('path', ('', )))}

        def __call__(self, url_path):
            if self.request.method.upper() != 'GET':
                # 405 Method Not Allowed
                raise self.method_not_allowed_response
            if self.is_file and url_path not in ('', None):
                # 404 Not Found
                raise self.not_found_response
            if self.is_file:
                os_path = self.path
            else:
                # get absolute path for resource requested
                os_path = os.path.abspath(os.path.join(self.path, url_path))
            if path < self.path:
                # 403 Forbidden
                raise self.forbidden_response
            # check if path is a file or directory and respond as appropriate
            if os.path.isdir(os_path):
                if self.request.url.path.endswith('/') == False and url_path != '':
                    raise self.not_found_response
                if self.expose_directories == False:
                    raise self.not_found_response
                self.response.body = _render_directory_template(
                    url_path, os_path, self.request.url.path
                )
            else:
                # return file to client
                self.response.content_type, _ = mimetypes.guess_type(os_path)
                # note, for gzip compression, we have to read the whole file into memory
                # ideally, we'd have a gzipped version on disk so that we could stream 
                # the file object using app_iter
                # this is a good task for the configure class method and a great future
                # enhancement
                try:
                    with open(os_path, 'rb') as f:
                        self.response.body = f.read()
                except IOError:
                    raise self.not_found_response
            return self.response
    
    Resource.path = os.path.abspath(path)
    Resource.is_file = os.path.isfile(path)
    Resource.expose_directories = expose_directories
    
    return Resource
