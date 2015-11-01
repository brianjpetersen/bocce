# standard libraries
import os
import mimetypes
import shutil
import hashlib
import gzip
import collections
import sqlite3
import datetime
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


_directory_template = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <title>Directory Listing for {full_url_path}</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css">
    <link href='http://fonts.googleapis.com/css?family=Lato&subset=latin,latin-ext' rel='stylesheet' type='text/css'>
    <style type="text/css">
        body{{background-color: #f1f1f1; font-family: Lato; color: #252226;}}
        hr{{color: #252226; background-color: #252226;}}
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


_error_template = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <title>{status}</title>
    <link href='http://fonts.googleapis.com/css?family=Lato&subset=latin,latin-ext' rel='stylesheet' type='text/css'>
    <style type="text/css">
        body{{background-color: #f1f1f1; font-family: Lato; color: #252226;}}
        hr{{color: #252226; background-color: #252226;}}
    </style>
  </head>
  <body>
    <h1>{status}</h1>
    <p>{message}</p>
  </body>
</html>'''


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


def mkdir(name):
    try:
        os.mkdir(name)
        os.chmod(name, 0o777)
    except:
        pass

def rm(name):
    try:
        os.chmod(name, 0o777)
        os.remove(name)
    except:
        pass


class CacheUndefined(Exception):
    
    pass


class FileIterator(object):
    
    def __init__(self, file_, block_size=4096):
        self.file_ = file_
        self.block_size = block_size
    
    def __iter__(self):
        block_size = self.block_size
        try:
            while True:
                block = self.file_.read(block_size)
                if not block:
                    break
                yield block
        finally:
            self.file_.close()


class File(object):
    
    FileStats = collections.namedtuple('FileStats', ('last_modified', 'size', 'content_type', 'block_size'))
    CacheStats = collections.namedtuple('CacheStats', ('last_modified', 'size', 'hash')) 
    
    def __init__(self, os_path, cache_directory):
        self.os_path = os_path
        self.cache_directory = cache_directory
        # setup sqlite connection for metadata
        cache_metadata_path = os.path.join(cache_directory, 'metadata.sqlite')
        self.connection = sqlite3.connect(cache_metadata_path)
        # setup os_stats and cache_stats
        self.os_stats = self.retrieve_os_stats()
        try:
            self.cache_stats = self.retrieve_cache_stats()
        except CacheUndefined:
            self.cache_stats = self.update_cache()
        # update cache if it's stale and cleanup any unneeded zip files
        if self.is_cache_stale:
            rm(self.zip_path)
            self.cache_stats = self.update_cache()
        # update cached zip file
        if os.path.isfile(self.zip_path) == False and self.should_be_zipped():
            self.update_zip_file()
    
    def should_be_zipped(self, accept_encoding=('gzip', )):
        return (
            (self.os_stats.size >= 128) and 
            (self.os_stats.content_type in mimetypes_to_compress) and
            ('gzip' in accept_encoding)
        )
        
    @property
    def file(self):
        file_ = open(self.os_path, 'rb')
        return FileIterator(file_, self.os_stats.block_size)
        
    @property
    def zip_file(self):
        file_ = open(self.zip_path, 'rb')
        return FileIterator(file_, self.os_stats.block_size)
    
    def update_zip_file(self):
        with open(self.os_path, 'rb') as source, gzip.open(self.zip_path, 'wb') as destination:
            shutil.copyfileobj(source, destination)
        os.chmod(self.zip_path, 0o777)
    
    @property
    def zip_path(self):
        hash_ = self.cache_stats.hash
        return os.path.join(self.cache_directory, 'zip/', '{}.gz'.format(hash_))
    
    @property
    def is_cache_stale(self):
        return (
            (self.os_stats.last_modified != self.cache_stats.last_modified) or 
            (self.os_stats.size != self.cache_stats.size)
        )
        
    def update_cache(self):
        self.hash = self.retrieve_hash()
        cache_stats = self.CacheStats(
            self.os_stats.last_modified, self.os_stats.size, self.hash
        )
        query = 'INSERT OR REPLACE INTO bocce VALUES(?, ?, ?, ?)'
        values = (self.os_path, cache_stats.last_modified, cache_stats.size, cache_stats.hash)
        connection = self.connection
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
        return cache_stats
    
    def retrieve_os_stats(self):
        content_type, _ = mimetypes.guess_type(self.os_path)
        os_stats = os.stat(self.os_path)
        file_size = os_stats.st_size
        file_last_modified = os_stats.st_mtime
        try:
            file_block_size = os_stats.st_blksize
        except:
            file_block_size = 4096
        return self.FileStats(file_last_modified, file_size, content_type, file_block_size)
        
    def retrieve_cache_stats(self):
        query = 'SELECT file_last_modified, file_size, file_hash FROM bocce \
                 WHERE os_path = "{}"'.format(self.os_path)
        cache_stats = self.connection.execute(query).fetchone()
        if cache_stats is None:
            raise CacheUndefined()
        else:
            file_last_modified, file_size, self.hash = cache_stats
            return self.CacheStats(file_last_modified, file_size, self.hash)
    
    @property
    def content_type(self):
        return self.os_stats.content_type
        
    @property
    def last_modified(self):
        return self.os_stats.last_modified
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args, **kwargs):
        self.connection.close()
    
    def retrieve_hash(self):
        hash_ = hashlib.md5()
        file_ = open(self.os_path, 'rb')
        for block in FileIterator(file_, self.os_stats.block_size):
            hash_.update(block)
        return hash_.hexdigest()


class Base(resources.Resource):
    
    @classmethod
    def configure_sqlite(cls):
        filename = os.path.join(cls.cache_directory, 'metadata.sqlite')
        connection = sqlite3.connect(filename)
        os.chmod(filename, 0o777)
        # create table if it doesn't exist
        with connection:
            cursor = connection.cursor()
            columns = 'os_path TEXT PRIMARY KEY, file_last_modified REAL, file_size REAL, file_hash TEXT'
            cursor.execute('CREATE TABLE IF NOT EXISTS bocce({columns})'.format(columns=columns))
        return connection
            
    @classmethod
    def configure(cls, configuration):
        super(Base, cls).configure(configuration)
        # pull relevant details out of configuration
        static_configuration = configuration.get('static', {})
        cls.expose_directories = static_configuration.get('expose_directories', False)
        cls.cleanup_cache = static_configuration.get('cleanup_cache', False)
        cls.max_age = static_configuration.get('max_age', 300)
        # create hidden directories
        if cls.is_file:
            path, _ = os.path.split(cls.path)
            cls.cache_directory = os.path.join(path, '.bocce/')
        else:
            cls.cache_directory = os.path.join(cls.path, '.bocce/')
        if cls.cleanup_cache:
            try:
                shutil.rmtree(cls.cache_directory)
            except OSError:
                pass
        mkdir(cls.cache_directory)
        zip_directory = os.path.join(cls.cache_directory, 'zip/')
        mkdir(zip_directory)
        # setup sqlite
        cls.configure_sqlite()
        if cls.is_file:
            os_path = cls.path
            with File(os_path, cls.cache_directory):
                pass
        else:
            # iterate over files in cls.path
            for base_directory, _, filenames in os.walk(cls.path, topdown=True):
                if '.' in base_directory:
                    continue
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    os_path = os.path.join(base_directory, filename)
                    with File(os_path, cls.cache_directory):
                        pass
    
    def _exception_response(self, status, message):
        response = exceptions.Response()
        response.status = status
        response.body = _error_template.format(
            status=status,
            message=message
        )
        return response
    
    @property
    def method_not_allowed_response(self):
        status = '405 Method Not Allowed'
        message = 'The method {} is not permitted on the requested URL {} \
                   on this server.'.format(str(self.request.url))
        return self._exception_response(status, message)
        
    @property
    def not_found_response(self):
        status = '404 Not Found'
        message = 'The requested URL {} was not found on this \
                   server.'.format(str(self.request.url))
        return self._exception_response(status, message)
        
    @property
    def forbidden_response(self):
        status = '403 Forbidden'
        message = 'Access to the requested URL {} is forbidden on this \
                   server.'.format(str(self.request.url))
        return self._exception_response(status, message)
        
    @property
    def not_modified_response(self):
        response = exceptions.Response()
        response.status = '304 Not Modified'
        return response
    
    def __enter__(self):
        return self, {'url_path': '/'.join(self.route.matches.get('path', ('', )))}

    def __call__(self, url_path):
        if self.configuration.get('secure', False):
            self.require_https()
            self.secure()
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
        if os_path < self.path:
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
            # return requested file
            try:
                file_ = File(os_path, self.cache_directory)
            except:
                raise self.not_found_response
            with file_:
                # check if request has etag validation that matches file_hash
                # return 304 Not Modified if so
                hash_ = file_.hash
                if hash_ in self.request.if_none_match:
                    raise self.not_modified_response
                # return zipped file
                if file_.should_be_zipped(self.request.accept_encoding):
                    self.response.app_iter = file_.zip_file
                    self.response.content_encoding = 'gzip'
                # return raw file
                else:
                    self.response.app_iter = file_.file
                self.response.content_type = file_.content_type
                self.response.etag = hash_
                self.response.cache_expires(self.max_age)
                # ideally would include this, but would need When to handle conversion to GMT
                #self.response.last_modified = file_.last_modified
        return self.response


def Resource(path, base=Base):
    
    class Resource(base):
        
        pass
    
    Resource.path = os.path.abspath(path)
    Resource.is_file = os.path.isfile(path)
        
    return Resource
