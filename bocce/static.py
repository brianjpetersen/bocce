# standard libraries
import os
import collections
import hashlib
import shutil
import gzip
import mimetypes
import sqlite3
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
        items.append((p, is_file))
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
        self.enable_compression(request)


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
        self.enable_compression(request)


class ForbiddenResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 403
        message = 'Access to the requested URL {} is forbidden on this server.'
        message = message.format(request.url.path)
        self.body.html = exception_template.format(
            status=self.status, message=message,
        )
        self.enable_compression(request)


class NotModifiedResponse(exceptions.Response):
    
    def handle(self, request, configuration):
        self.status_code = 304



class Path:
    
    def __init__(self, path):
        self.path = os.path.abspath(os.path.normpath(path))
        self.is_file = os.path.isfile(self.path)
        self.is_directory = os.path.isdir(self.path)
        if self.is_file:
            self.directory = os.path.dirname(self.path)
            self._stats = os.stat(self.path)
            self.size = getattr(self._stats, 'st_size', None)
            self.last_modified = getattr(self._stats, 'st_mtime', None)
            self.block_size = getattr(self._stats, 'st_blksize', 4096)
            self.mimetype, _ = mimetypes.guess_type(self.path)
        else:
            self.directory = self.path

    def join(self, *p):
        return self.__class__(os.path.join(self.path, *p))
    
    def is_below(self, other):
        return self.path.startswith(os.path.normpath(other.path))
    
    def is_above(self, other):
        return os.path.normpath(other.path).startswith(self.path)
    
    @property
    def file_iterator(self):
        if self.is_directory:
            raise TypeError
        file_iterator = responses.FileIterator(self.path, 'rb', self.block_size)
        return iter(file_iterator)


class CachedPath(Path):
    
    def __init__(self, path, cache_directory=None):
        super(CachedPath, self).__init__(path)
        if cache_directory is None:
            self.cache_directory = os.path.join(self.directory, '.bocce')
        else:
            self.cache_directory = cache_directory
        self.cache_filename = os.path.join(self.cache_directory, 'bocce.sqlite')
        self.setup_cache_directory()
        # retrieve data from cache
        if self.is_file:
            query = 'SELECT last_modified, size, etag \
                     FROM bocce WHERE path = "{}"'.format(self.path)
            connection = sqlite3.connect(self.cache_filename)
            with connection:
                values = connection.execute(query).fetchone()
            connection.close()
            if values is None:
                self.update_cache()
            else:
                # overwrite os stats with cached stats
                self.last_modified, self.size, self.etag = values
            if self.cache_stale:
                self.update_cache()
    
    def clean_cache(self):
        rmdir(self.cache_directory)
    
    def setup_cache_directory(self):
        mkdir(self.cache_directory)
        connection = sqlite3.connect(self.cache_filename)
        os.chmod(self.cache_filename, 0o777)
        # create table if it doesn't exist
        columns = ', '.join((
            'path TEXT PRIMARY KEY',
            'last_modified REAL',
            'size INTEGER',
            'etag TEXT',
        ))
        query = 'CREATE TABLE IF NOT EXISTS bocce({})'.format(columns)
        with connection:
            cursor = connection.cursor()
            cursor.execute(query)
        connection.close()
    
    @property
    def cache_stale(self):
        os_size = getattr(self._stats, 'st_size', None)
        os_last_modified = getattr(self._stats, 'st_mtime', None)
        fresh = os_size == self.size and os_last_modified == self.last_modified
        return not fresh
    
    def cache_below(self, threads=None):
        # if self is a file, it has already been cached
        if self.is_file:
            raise TypeError
        # if self is a directory, walk it and instantiate each CachedPath object
        # which will compress and hash the files
        with futures.ThreadPoolExecutor(max_workers=threads) as executor:
            walk = lambda: os.walk(self.directory, topdown=True)
            for base_directory, _, filenames in walk():
                if '.' in base_directory:
                    continue
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    path = os.path.join(base_directory, filename)
                    executor.submit(self.__class__, path, self.cache_directory)
    
    def update_cache(self):
        if self.is_directory:
            raise TypeError()
        self.size = getattr(self._stats, 'st_size', None)
        self.last_modified = getattr(self._stats, 'st_mtime', None)
        self.block_size = getattr(self._stats, 'st_blksize', 4096)
        self.mimetype, _ = mimetypes.guess_type(self.path)
        # compress and hash file
        hashed_path = str(hash(self.path))
        temporary_filename = os.path.join(self.cache_directory, hashed_path)
        etag = hashlib.md5()
        block_size = self.block_size
        open_gzip = lambda: gzip.open(temporary_filename, 'wb', 9)
        open_path = lambda: open(self.path, 'rb')
        with open_path() as path_file, open_gzip() as compressed_file:
            while True:
                block = path_file.read(block_size)
                if not block:
                    break
                compressed_file.write(block)
                etag.update(block)
        self.etag = etag.hexdigest()
        permanent_filename = os.path.join(self.cache_directory, self.etag)
        shutil.move(temporary_filename, permanent_filename)
        os.chmod(permanent_filename, 0o777)
        # update sqlite cache metadata
        query = 'INSERT OR REPLACE INTO bocce VALUES(?, ?, ?, ?)'
        values = (
            self.path,
            self.last_modified,
            self.size,
            self.etag,
        )
        connection = sqlite3.connect(self.cache_filename)
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
        connection.close()
    
    def join(self, *p):
        return self.__class__(os.path.join(self.path, *p), self.cache_directory)
    
    @property
    def file_iterator(self):
        if self.is_directory:
            raise TypeError
        file_iterator = responses.FileIterator(self.path, 'rb', self.block_size)
        return iter(file_iterator)
    
    @property
    def compressed_path(self):
        if self.is_directory:
            raise TypeError
        compressed_path = os.path.join(self.cache_directory, self.etag)
        return Path(compressed_path)


class Response(responses.Response):
    
    def __init__(self, path, clean=False, threads=None, expose_directory=False, 
                 cache_directory=None):
        super(Response, self).__init__()
        self.path = CachedPath(path, cache_directory)
        self.expose_directory = expose_directory
        if clean:
            self.path.clean_cache()
        if self.path.is_directory:
            self.path.cache_below(threads)
    
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
                except OSError:
                    raise NotFoundResponse()
        # if the full path is a file, serve it; else, either serve directory html
        # if directories are exposed, or throw a 403
        if path.is_file:
            # throw 403 if the path is above the mounting path in the filesystem 
            if path.is_above(self.path):
                raise ForbiddenResponse()
            # set etag header and check if client has cached this content
            if path.etag in request.cache.if_none_match:
                raise NotModifiedResponse()
            # see if we have compressed content, and if not, create it
            compressed_path = path.compressed_path
            # check if we can return compressed content
            if 'gzip' in request.accept.encodings:
                # check if we should compress
                if compressed_path.size < path.size and path.mimetype in mimetypes_to_compress:
                    self.body.set_iterable(
                        iter(compressed_path.file_iterator),
                        content_length=compressed_path.size,
                        mimetype=path.mimetype,
                    )
                    self.headers.replace('Content-Encoding', 'gzip')
                # shouldn't return compressed file
                else:
                    self.body.set_iterable(
                        iter(path.file_iterator),
                        content_length=path.size,
                        mimetype=path.mimetype,
                    )
            # can't return compressed file
            else:
                self.body.set_iterable(
                    iter(path.file_iterator),
                    content_length=path.size,
                    mimetype=path.mimetype,
                )
            self.headers.replace('Etag', path.etag)
        elif path.is_directory:
            if self.expose_directory:
                self.body.set_html(
                    render_directory_template(path.path, request.url.path)
                )
            else:
                raise ForbiddenResponse()
        else:
            raise NotFoundResponse()
        
