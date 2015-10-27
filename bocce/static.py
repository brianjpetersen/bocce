# standard libraries
import os
import mimetypes
import posixpath
import gzip
import shutil
# third party libraries
pass
# first party libraries
from . import (responses, resources, exceptions, )


__all__ = ('Resource', '__where__', )
__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


mimetypes_to_compress = set(
    ('text/html', 'application/x-javascript', 'text/css', 'application/javascript', 'text/javascript', 
     'text/plain', 'text/xml', 'application/json', 'application/x-font-opentype', 
     'application/x-font-truetype', 'application/x-font-ttf', 'application/xml', 
     'font/eot', 'font/opentype', 'font/otf', 'image/svg+xml', 'image/vnd.microsoft.icon')
)


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


class FileIterator(object):
    
    def __init__(self, file, block_size):
        self.file = file
        self.block_size = block_size
        
    def __iter__(self):
        try:
            while True:
                block = self.file.read(self.block_size)
                if not block:
                    break
                yield block
        finally:
            self.file.close()


def Resource(path, expose_directories=False, prezip_files=False, cache_content):
    
    class Resource(resources.Resource):
        
        base_zip_cache_directory = '.bocce-zip-cache/'
        
        @classmethod
        def configure(cls, configuration):
            super(Resource, cls).configure(configuration)

        def __init__(self, request, route):
            super(Resource, self).__init__(request, route)
            self.response = responses.Response()

        @property
        def method_not_allowed_response(self):
            response = exceptions.Response()
            
        @property
        def not_found_response(self):
            pass
            
        @property
        def forbidden_response(self):
            pass
        
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
            # check if path is a file or directory and respond appropriately
            if os.path.isdir(os_path):
                if self.request.url.path.endswith('/') == False and url_path != '':
                    raise self.not_found_response
                if self.expose_directories == False:
                    raise self.not_found_response
                self.response.body = _render_directory_template(
                    url_path, os_path, self.request.url.path
                )
            else:
                # get metadata
                content_type, _ = mimetypes.guess_type(os_path)
                self.response.content_type = content_type
                stats = os.stat(os_path)
                file_size = stats.st_size
                when_last_modified = stats.st_mtime
                
                try:
                    block_size = stats.st_blksize
                except:
                    block_size = 4096
                # determine if the file should be compressed
                should_be_zipped = (
                    'gzip' in self.request.accept_encoding and file_size > 999 and 
                    content_type in mimetypes_to_compress
                )
                if should_be_zipped:
                    # check to see if zip file already exists
                    directory, filename = os.path.split(os_path)
                    # does the directory exist?  create if not.
                    cache_directory = os.path.join(directory, self.base_zip_cache_directory)
                    if os.path.isdir(cache_directory) == False:
                        os.mkdir(cache_directory)
                    # does the zip file exist?  create if not.
                    last_modified_timestamp = str(when_last_modified).replace('.', '').strip()
                    base_filename, extension = os.path.splitext(filename)
                    compressed_filename = '.{}-{}{}.gz'.format(
                        base_filename, last_modified_timestamp, extension
                    )
                    compressed_path = os.path.join(cache_directory, compressed_filename)
                    try:
                        file_ = open(compressed_path, 'rb')
                        self.response.content_encoding = 'gzip'
                    except IOError:
                        try:
                            with open(os_path, 'rb') as f_in, gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                            file_ = gzip.open(compressed_path, 'rb')
                            self.response.content_encoding = 'gzip'
                        except:
                            try:
                                file_ = open(os_path, 'rb')
                            except IOError:
                                raise self.not_found_response
                else:
                    try:
                        file_ = open(os_path, 'rb')
                    except IOError:
                        raise self.not_found_response
                self.response.app_iter = FileIterator(file_, block_size)
            return self.response
    
    Resource.path = os.path.abspath(path)
    Resource.is_file = os.path.isfile(path)
    Resource.expose_directories = expose_directories
    Resource.prezip_files = prezip_files
    
    return Resource
