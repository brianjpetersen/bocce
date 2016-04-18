# standard libraries
import os
import collections
import hashlib
import shutil
import gzip
import mimetypes
import concurrent.futures as futures
# third party libraries
pass
# first party libraries
from . import (exceptions, responses, )


__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


mimetypes_to_compress = set(
    ('text/html', 'application/x-javascript', 'text/css', 
     'application/javascript', 'text/javascript', 'text/plain', 'text/xml', 
     'application/json', 'application/x-font-opentype', 
     'application/x-font-truetype', 'application/x-font-ttf', 'application/xml', 
     'font/eot', 'font/opentype', 'font/otf', 'image/svg+xml', 
     'image/vnd.microsoft.icon')
)


directory_template = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <title>Directory Listing for {path}</title>
        <link rel="stylesheet" href="https://goo.gl/VyJGqZ">
        <link href='https://fonts.googleapis.com/css?family=Varela+Round'
              rel='stylesheet' type='text/css'>
        <style type="text/css">
            body{{
                background-color: #f1f1f1;
                font-family: 'Varela Round', sans-serif;
                color: #252226;
            }}
            hr{{
                color: #252226;
                background-color: #252226;
            }}
        </style>
    </head>
    <body>
        <h1>Directory Listing for {path}</h1>
        <hr>
        <ul class="fa-ul">
            {directories}
        </ul>
        <hr>
  </body>
</html>
'''


directory_list_item_template = '''
<li>
    {icon}<a href="{path}">{path}</a>
</li>
'''


exception_template = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <title>{status}</title>
        <link href='https://fonts.googleapis.com/css?family=Varela+Round'
              rel='stylesheet' type='text/css'>
        <link href='https://fonts.googleapis.com/css?family=Roboto+Mono' 
              rel='stylesheet' type='text/css'>
        <style type="text/css">
            body{{
                background-color: #f1f1f1;
                font-family: 'Varela Round', sans-serif;
                color: #252226;
            }}
            hr{{
                color: #252226;
                background-color: #252226;
            }}
        </style>
    </head>
    <body>
        <h1>{status}</h1>
        <p>{message}</p>
    </body>
</html>
'''


def render_directory_list_item(path, is_file):
    if is_file:
        icon = '<i class="fa-li fa fa-file"></i>'
    else:
        if path.endswith('/') == False:
            path = path + '/'
        icon = '<i class="fa-li fa fa-folder"></i>'
    return directory_list_item_template.format(path=path, icon=icon)


def render_directory_template(path, url_path):
    items = []
    for p in os.listdir(path):
        if p.startswith('.'):
            continue
        is_file = os.path.isfile(os.path.join(path, p))
        items.append((is_file, p))
    items.sort()
    directories = []
    for p, is_file in items:
        directories.append(render_directory_list_item(p, is_file))
    return directory_template.format(
        directories='\n'.join(directories),
        path=url_path,
    )


def mkdir(name):
    try:
        os.mkdir(name)
        os.chmod(name, 0o777)
    except:
        pass


def rm(filename):
    try:
        os.chmod(filename, 0o777)
        os.remove(filename)
    except:
        pass


def rmdir(directory):
    try:
        shutil.rmtree(directory)
    except OSError:
        pass


class NotFoundResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 404
        message = 'The requested URL /{} was not found on this server.'
        message = message.format(request.url.path)
        self.body.html = exception_template.format(
            status=self.status, message=message,
        )


class MethodNotAllowedResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 405
        self.headers['Allow'] = 'GET'
        message = 'The method {} is not permitted on the requested URL /{} ' \
           'on this server.'
        message = message.format(request.http.method, request.url.path)
        self.body.html = exception_template.format(
            status=self.status, message=message,
        )


class ForbiddenResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 403
        message = 'Access to the requested URL {} is forbidden on this server.'
        message = message.format(request.url.path)
        self.body.html = exception_template.format(
            status=self.status, message=message,
        )


class NotModifiedResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 304


class Path:
    
    def __init__(self, path):
        self.path = os.path.normpath(path)
        self.is_file = os.path.isfile(path)
        self.is_directory = not self.is_file
        if self.is_file:
            self.directory = os.path.dirname(path)
        else:
            self.directory = path
        self.mimetype, _ = mimetypes.guess_type(self.path)
        stats = os.stat(self.path)
        self.size = getattr(stats, 'st_size', None)
        self.last_modified = getattr(stats, 'st_mtime', None)
        self.block_size = getattr(stats, 'st_blksize', 4096)
    
    @property
    def etag(self):
        h = hashlib.md5()
        h.update(self.path.encode('utf-8'))
        h.update(str(self.size).encode('utf-8'))
        h.update(str(self.last_modified).encode('utf-8'))
        return h.hexdigest()
    
    def join(self, *p):
        return self.__class__(os.path.join(self.path, *p))
    
    def is_below(self, other):
        return self.path.startswith(os.path.normpath(other.path))
    
    def is_above(self, other):
        return os.path.normpath(other.path).startswith(self.path)
    
    def compress(self, destination, level=2):
        block_size = self.block_size
        with open(self.path, 'rb') as s, gzip.open(destination, 'wb', level) as d:
            while True:
                block = s.read(block_size)
                if not block:
                    break
                d.write(block)
        os.chmod(destination, 0o777)
    
    def walk(self):
        if self.is_file:
            yield self
        else:
            for base_directory, _, filenames in os.walk(self.path, topdown=True):
                if '.' in base_directory:
                    continue
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    path = os.path.join(base_directory, filename)
                    yield self.__class__(path)
    
    @property
    def file_iterator(self):
        if self.is_directory:
            raise TypeError
        return responses.FileIterator(self.path, 'rb', self.block_size)


class Response(responses.Response):
    
    def __init__(self, path, cache=True, clean=False, threads=None,
                 expose_directory=False):
        super(Response, self).__init__()
        self.path = Path(os.path.abspath(path))
        self.cache_directory = os.path.join(self.path.directory, '.bocce')
        self.expose_directory = expose_directory
        if clean:
            self.clean_cache(self.cache_directory)
        if cache:
            self.setup_cache(self.path, self.cache_directory, threads)
    
    @staticmethod
    def clean_cache(cache_directory):
        rmdir(cache_directory)
    
    @staticmethod
    def setup_cache(path, cache_directory, threads=None):
        mkdir(cache_directory)
        with futures.ThreadPoolExecutor(max_workers=threads) as executor:
            for child in path.walk():
                if child.is_directory:
                    continue
                compressed_filename = os.path.join(cache_directory, child.etag)
                if os.path.exists(compressed_filename) == False:
                    executor.submit(child.compress, compressed_filename)
    
    def handle(self, request, configuration):
        if request.http.method not in ('HEAD', 'GET'):
            raise MethodNotAllowedResponse()
        # we will handle the compression and compression headers manually
        self.compress = False
        # construct full path, joining with any included as part of url
        if self.path.is_file:
            path = self.path
        else:
            subpath = request.segments.get('path', None)
            if subpath is None:
                path = self.path
            else:
                # if path joining generates an exception, it doesn't exist
                try:
                    path = self.path.join(subpath)
                except:
                    raise NotFoundResponse()
        # if the full path is a file, serve it; else, either serve directory html
        # if directories are exposed, or throw a 403
        if path.is_file:
            # throw 403 if the path is above the mounting path in the filesystem 
            if path.is_above(self.path):
                raise ForbiddenResponse()
            # check if client has cached this content
            if path.etag in request.cache.if_none_match:
                raise NotModifiedResponse()
            # see if we have compressed content, and if not, create it
            compressed_filename = os.path.join(self.cache_directory, path.etag)
            try:
                compressed_path = Path(compressed_filename)
            except:
                path.compress(compressed_filename)
                compressed_path = Path(compressed_filename)
            # check if we can return compressed content
            if 'gzip' in request.accept.encodings:
                # check if we should compress
                if compressed_path.size < path.size:
                    self.body.set_iterable(
                        iter(compressed_path.file_iterator),
                        content_length=compressed_path.size,
                        mimetype=path.mimetype,
                    )
                    self.headers.replace('Content-Encoding', 'gzip')
                # shouldn't compress
                else:
                    self.body.set_iterable(
                        iter(path.file_iterator),
                        content_length=path.size,
                        mimetype=path.mimetype,
                    )
            # can't compress
            else:
                self.body.set_iterable(
                    iter(path.file_iterator),
                    content_length=path.size,
                    mimetype=path.mimetype,
                )
            self.headers['Etag'] = path.etag
        elif path.is_directory:
            if self.expose_directory:
                self.body.set_html(
                    render_directory_template(path.path, request.url.path)
                )
                
            else:
                raise ForbiddenResponse()
