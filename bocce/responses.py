# standard libraries
import os
import abc
import collections
import copy
import io
import gzip
import mimetypes
import datetime
# third party libraries
import numpy
import werkzeug
# first party libraries
from . import (surly, utils, headers, cookies, )


__where__ = os.path.dirname(os.path.abspath(__file__))


mimetypes._winreg = None # do not load mimetypes from windows registry
mimetypes.add_type('text/javascript', '.js') # stdlib default is application/x-javascript
mimetypes.add_type('image/x-icon', '.ico') # not among defaults


class FileIterator:
    
    def __init__(self, filename, mode='rb', block_size=None):#, delete_after=False):
        self.filename = filename
        if block_size is None:
            stats = self.stats = os.stat(filename)
            block_size = getattr(stats, 'st_blksize', 4096)
        self.file_ = open(filename, mode)
        self.block_size = block_size
        #self.delete_after = delete_after
    
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
        """
        if self.delete_after:
            try:
                os.remove(self.filename)
            except:
                pass
        """

class BodyIterable:
    
    def __init__(self, iterable, content_length, content_type, content_encoding):
        self.iterable = iterable
        self.content_length = content_length
        self.content_type = content_type
        self.content_encoding = content_encoding
    
    @property
    def wsgi(self):
        return self.iterable


class BodyFile(BodyIterable):
    
    def __init__(self, filename, mimetype=None, charset=None, is_compressed=False):
        self.filename = filename
        self.iterable = FileIterator(self.filename)
        self.content_length = getattr(self.iterable.stats, 'st_size', None)
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(self.filename)
        if mimetype is None:
            self.content_type = None
        else:
            if charset is None:
                self.content_type = mimetype
            else:
                self.content_type = '{}; {}'.format(mimetype, charset)
        self.is_compressed = is_compressed
        if self.is_compressed:
            self.content_encoding = 'gzip'
        else:
            self.content_encoding = None
    
    """
    def compress(self, level=2, threshold=128):
        
        if len(self._content) < threshold:
            return 
    """
    
    @property
    def wsgi(self):
        return self.iterable


class BodyContent:
    
    def __init__(self, content, content_type):
        self._content = content
        self.content_type = content_type
        self.content_encoding = None
    
    @property
    def content(self):
        if self.content_encoding == 'gzip':
            return self._compressed_content
        else:
            return self._content
    
    @property
    def content_length(self):
        return len(self.content)
    
    def compress(self, level=2, threshold=128):
        if len(self._content) < threshold:
            return
        compressed_content = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed_content, mode='wb', compresslevel=level) as f:
            f.write(self._content)
        self._compressed_content = compressed_content.getvalue()
        self.content_encoding = 'gzip'
    
    @property
    def wsgi(self):
        return [self.content, ]


class JsonBody(collections.OrderedDict):
    
    def __init__(self, charset='utf-8', indent=None, serializers=None):
        super(JsonBody, self).__init__()
        if serializers is None:
            serializers = {}
            serializers[surly.Url] = lambda url: str(url)
            serializers[tuple] = lambda tuple: list(tuple)
            serializers[set] = lambda set: list(set)
            serializers[datetime.date] = lambda date: date.isoformat()
            serializers[datetime.datetime] = lambda datetime: datetime.isoformat()
            serializers[bytes] = lambda bytes: bytes.decode(charset)
            serializers[numpy.ndarray] = lambda array: array.tolist()
        self.serializers = serializers
        self.indent = indent
        self.charset = charset
        self.content_type = 'application/json; charset={}'.format(charset)
        self.content_encoding = None
        self._cached_content = None
        self._compression_level = None
        self._compression_threshold = None
        self._compression_requested = False
    
    def __setitem__(self, *args, **kwargs):
        self._cached_content = None
        super(JsonBody, self).__setitem__(*args, **kwargs)
        
    def __getitem__(self, *args, **kwargs):
        self._cached_content = None
        return super(JsonBody, self).__getitem__(*args, **kwargs)
    
    @property
    def content_length(self):
        return len(self.content)
    
    @property
    def content(self):
        if self._cached_content is not None:
            return self._cached_content
        encoder = utils.JsonEncoder(self.indent, self.serializers)
        content = encoder.encode(self).encode(self.charset)
        # attempt to compress
        compression_threshold = getattr(self, '_compression_threshold', 128)
        compression_level = getattr(self, '_compression_level', 2)
        compression_requested = getattr(self, '_compression_requested', False)
        if compression_requested and len(content) >= compression_threshold:
            compressed_content = io.BytesIO()
            with gzip.GzipFile(fileobj=compressed_content, mode='wb', compresslevel=compression_level) as f:
                f.write(content)
            content = compressed_content.getvalue()
            self.content_encoding = 'gzip'
        self._cached_content = content
        return content
    
    def compress(self, level=2, threshold=128):
        self._cached_content = None
        self._compression_level = level
        self._compression_threshold = threshold
        self._compression_requested = True
    
    @property
    def wsgi(self):
        return [self.content, ]


class Body:
    
    def __init__(self):
        self.set_content(bytes())
    
    @property
    def content_length(self):
        content_length = getattr(self._iterable, 'content_length', None)
        if content_length is not None:
            content_length = str(content_length)
        return content_length
    
    @property
    def content_type(self):
        content_type = getattr(self._iterable, 'content_type', None)
        if content_type is not None:
            content_type = str(content_type)
        return content_type
    
    @property
    def content_encoding(self):
        content_encoding = getattr(self._iterable, 'content_encoding', None)
        if content_encoding is not None:
            content_encoding = str(content_encoding)
        return content_encoding
    
    def compress(self, *args):
        self._iterable.compress(*args)
    
    def set_file(self):
        raise NotImplementedError
    
    def get_json(self):
        if not isinstance(self._iterable, JsonBody):
            self.set_json({})
        return self._iterable
    
    def set_json(self, value=None, charset='utf-8', indent=None, serializers=None):
        previous_json_body = getattr(self, '_iterable', None)
        if value is None:
            value = {}
        self._iterable = JsonBody(charset, indent, serializers)
        if previous_json_body is not None:
            if isinstance(previous_json_body, JsonBody):
                level = previous_json_body._compression_level
                threshold = previous_json_body._compression_threshold
                requested = previous_json_body._compression_requested
                self._iterable._compression_level = level
                self._iterable._compression_threshold = threshold
                self._iterable._compression_requested = requested
        self._iterable.update(value)
    
    def set_html(self, html, charset='utf-8'):
        self.set_text(html, mimetype='text/html', charset=charset)
    
    def set_text(self, text, mimetype='text/plain', charset='utf-8'):
        if mimetype is None:
            content_type = None
        else:
            if charset is None:
                content_type = mimetype
            else:
                content_type = '{}; {}'.format(mimetype, charset)
        self.set_content(text.encode(charset), content_type)
    
    def set_content(self, content, content_type=None):
        self._iterable = BodyContent(content, content_type)
    
    def set_iterable(self, iterable, content_length=None, content_type=None,
                     content_encoding=None):
        self._iterable = BodyIterable(iterable, content_length, content_type, content_encoding)
    
    def __iter__(self):
        return iter(self._iterable.wsgi)
    
    content = property(fset=set_content)
    text = property(fset=set_text)
    json = property(fget=get_json, fset=set_json)
    html = property(fset=set_html)
    #file = property(fset=set_file)


class Response:
    
    def __init__(self):
        self.status_code = 200
        self.body = Body()
        self.cookies = cookies.ResponseCookies()
        self.headers = headers.DelegatedResponseHeaders(
            headers.CookiesResponseHeadersView(self.cookies),
            headers.BodyResponseHeadersView(self.body),
        )
    
    @property
    def status(self):
        status_code = self.status_code
        return '{} {}'.format(
            status_code, werkzeug.http.HTTP_STATUS_CODES[status_code]
        )
    
    def start(self, start_response):
        start_response(self.status, list(self.headers))
        return self.body
