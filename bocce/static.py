# standard libraries
import os
import collections
import hashlib
import shutil
import gzip
#import sqlite3
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
        <title>Directory Listing for {full_url_path}</title>
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
        <h1>Directory Listing for {full_url_path}</h1>
        <hr>
        <ul class="fa-ul">
            {directory_list}
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


def render_directory_template(url_path, os_path, full_url_path):
    items = []
    for path in os.listdir(os_path):
        if path.startswith('.'):
            continue
        is_file = os.path.isfile(os.path.join(os_path, path))
        items.append((is_file, path))
    items.sort()
    directory_list = []
    for path, is_file in items:
        directory_list.append(render_directory_list_item(path, is_file))
    return directory_template.format(
        url_path=url_path,
        directory_list='\n'.join(directory_list),
        full_url_path=full_url_path,
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


class CacheUndefined(Exception):
    
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

"""
class CachedPath:
    
    def __init__(self, path, cache_filename='./.bocce/bocce.sqlite'):
        self.path = path
        self.connection = sqlite3.connect(cache_filename)
        query = 'SELECT last_modified, size, etag FROM bocce \
                 WHERE path = "{}"'.format(self.path)
        values = self.connection.execute(query).fetchone()
        if values is None:
            raise CacheUndefined()
        else:
            self.last_modified, self.size, self.etag = values
        
    def update_from_path(self, path):
        assert path.path == self.path
        query = 'INSERT OR REPLACE INTO bocce VALUES(?, ?, ?, ?)'
        values = (self.path, path.last_modified, path.size, path.etag, )
        connection = self.connection
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
"""

class Path:
    
    def __init__(self, path):
        self.path = path
        self.is_file = os.path.isfile(path)
        self.is_directory = not self.is_file
        if self.is_file:
            self.directory = os.path.dirname(path)
        else:
            self.directory = path
        self.content_type, _ = mimetypes.guess_type(self.path)
        stats = os.stat(self.path)
        self.size = stats.st_size
        self.last_modified = stats.st_mtime
        self.block_size = getattr(stats, 'st_blksize', 4096)
    
    @property
    def etag(self):
        return hash(self)
    
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
    
    def __iter__(self):
        if self.is_directory:
            raise TypeError
        return responses.FileIterator(self.path, 'rb', self.block_size)
    
    def __hash__(self):
        h = hashlib.md5()
        h.update(self.path.encode('utf-8'))
        h.update(str(self.size).encode('utf-8'))
        h.update(str(self.last_modified).encode('utf-8'))
        return h.hexdigest()
    
    def __eq__(self, other):
        return self.etag == other.etag


class Response(responses.Response):
    
    def __init__(self, path, cache=True, clean=False, threads=None, 
                 compression_threshold=128):
        super(Response, self).__init__()
        self.path = Path(path)
        self.cache_directory = os.path.join(self.path.directory, '.bocce')
        self.cache_compression_threshold = compression_threshold
        if clean:
            self.clean_cache(self.cache_directory)
        if cache:
            self.setup_cache(
                self.path,
                self.cache_directory,
                threads,
            )
    
    """
    @staticmethod
    def setup_sqlite(cache_directory):
        cache_filename = os.path.join(cache_directory, 'bocce.sqlite')
        connection = sqlite3.connect(cache_filename)
        os.chmod(cache_filename, 0o777)
        # create table if it doesn't exist
        columns = ', '.join((
            'path TEXT PRIMARY KEY',
            'last_modified REAL',
            'size REAL',
            'etag TEXT',
        ))
        query = 'CREATE TABLE IF NOT EXISTS bocce({})'.format(columns)
        with connection:
            cursor = connection.cursor()
            cursor.execute(query)
        connection.close()
    """
    
    @staticmethod
    def clean_cache(cache_directory):
        rmdir(cache_directory)
    
    @staticmethod
    def setup_cache(path, cache_directory, threads=None):
        mkdir(cache_directory)
        #Response.setup_sqlite(cache_directory)
        #compressed_directory = os.path.join(cache_directory, 'zip')
        #mkdir(compressed_directory)
        with futures.ThreadPoolExecutor(max_workers=threads) as executor:
            for child_path in path.walk():
                if child_path.is_directory:
                    continue
                executor.submit(
                    Response.cache_path,
                    child_path,
                    cache_directory,
                )
    
    @staticmethod
    def cache_path(path, cache_directory):
        pass
    
    def handle(self, request, configuration):
        pass
