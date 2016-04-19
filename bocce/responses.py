# standard libraries
import os
import abc
import collections
import copy
import json
import io
import gzip
import mimetypes
# third party libraries
import werkzeug
# first party libraries
from . import (logging, surly, utils, headers, )


__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


class FileIterator(object):
    
    def __init__(self, filename, mode='rb', block_size=None):
        if block_size is None:
            stats = os.stat(filename)
            block_size = getattr(stats, 'st_blksize', 4096)
        self.file_ = open(filename, mode)
        self.block_size = block_size
    
    def __iter__(self):
        block_size = self.block_size
        file_ = self.file_
        try:
            while True:
                block = file_.read(block_size)
                if not block:
                    break
                yield block
        finally:
            file_.close()


class JSONEncoder(json.JSONEncoder):
    
    def __init__(self, indent=None, **serializers):
        super(JSONEncoder, self).__init__(indent=indent)
        self.serializers = serializers
    
    def default(self, obj):
        try:
            serializer = self.serializers[obj.__class__.__name__]
            return serializer(obj)
        except:
            return super(JSONEncoder, self).default(obj)


class Body:
    
    def __init__(self, headers):
        self.headers = headers
        self.set_content(bytes())
    
    def compress(self, level=2, threshold=128):
        if self._can_compress == False:
            raise ValueError
        if self.content_length < threshold:
            return
        content = io.BytesIO()
        with gzip.GzipFile(fileobj=content, mode='wb', compresslevel=level) as f:
            f.write(self.content)
        self.set_content(content.getvalue(), self.mimetype, self.charset)
        self.headers.replace('Content-Encoding', 'gzip')
        self._can_compress = False
    
    def set_content_type(self, mimetype, charset=None):
        if mimetype is None:
            try:
                del self.headers['Content-Type']
            except:
                pass
            finally:
                self.content_type = None
                self.mimetype = None
                self.charset = charset
        else:
            mimetype = self.mimetype = mimetype.strip()
            content_type = mimetype
            if charset is not None:
                self.charset = charset
                content_type += '; charset={}'.format(charset)
            self.content_type = content_type
            self.headers.replace('Content-Type', content_type)
    
    def set_content_length(self, content_length):
        if content_length is None:
            try:
                del self.headers['Content-Length']
            finally:
                self.content_length = None
        else:
            self.content_length = content_length
            self.headers.replace('Content-Length', content_length)
    
    def set_iterable(self, iterable, content_length=None, mimetype=None,
                     charset=None):
        self.set_content_type(mimetype, charset)
        self.set_content_length(content_length)
        self.iterable = iterable
    
    def set_json(self, d, charset='utf-8', indent=None, **serializers):
        if 'date' not in serializers:
            serializers['date'] = lambda date: date.isoformat()
        if 'datetime' not in serializers:
            serializers['datetime'] = lambda datetime: datetime.isoformat()
        encoder = JSONEncoder(indent, **serializers)
        text = encoder.encode(d)
        mimetype = 'application/json'
        self.set_text(text, mimetype, charset)
    
    def set_content(self, content, mimetype=None, charset=None):
        try:
            del self.headers['Content-Encoding']
        except:
            pass
        self.content = content
        iterable = iter([content, ])
        content_length = len(content)
        self.set_iterable(iterable, content_length, mimetype, charset)
        self._can_compress = True
    
    def set_text(self, text, mimetype='text/plain', charset='utf-8'):
        self.set_content(text.encode(charset), mimetype, charset)
    
    def set_html(self, html, charset='utf-8'):
        mimetype = 'text/html'
        self.set_text(html, mimetype, charset)
    
    def set_file(self, filename, file_mode='rb', mimetype=None, charset=None, 
                 is_compressed=False):
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)
        stats = os.stat(filename)
        content_length = stats.st_size
        block_size = stats.st_blksize
        file_iterator = FileIterator(filename, file_mode, block_size)
        self.set_iterable(
            iter(file_iterator),
            content_length,
            mimetype,
            charset,
        )
        if is_compressed:
            self.headers.replace('Content-Encoding', 'gzip')
    
    def __iter__(self):
        return self.iterable
    
    text = property(fset=set_text)
    json = property(fset=set_json)
    html = property(fset=set_html)
    file = property(fset=set_file)


class Response:
    
    def __init__(self, before=None, after=None, configure=None):
        if before is None:
            before = []
        before.insert(0, self._setup_response_entities)
        if after is None:
            after = [logging.log, ]
        if configure is None:
            configure = []
        self.configure = configure
        self.before = before
        self.after = after
        
    @staticmethod
    def _setup_response_entities(request, response, configuration):
        # abstract over response
        response.headers = headers.ResponseHeaders()
        response.status_code = 200
        response.body = Body(response.headers)
        response.compress = False
    
    def enable_compression(self, request, level=2, threshold=128):
        if 'gzip' in request.accept.encoding:
            self.compress = True
            self.compression_threshold = threshold
            self.compression_level = level
    
    @property
    def cookies(self):
        return self.headers.cookies
    
    @property
    def status(self):
        status_code = self.status_code
        return '{} {}'.format(
            status_code, werkzeug.http.HTTP_STATUS_CODES[status_code]
        )
    
    def handle(self, request, configuration):
        pass
    
    def start(self, start_response):
        if self.compress:
            self.body.compress(
                self.compression_level,
                self.compression_threshold,
            )
        start_response(self.status, list(self.headers))
        return self.body
