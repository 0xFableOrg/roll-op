"""
This modules contains classes defining "streams", which implement the `write(text)` and `flush()`
methods, as well as `close()` and `closed` (though those do not seem required), making them usable
in place of file descriptors for functions such as subprocess.Popen, or assignable to `sys.stdout`.
"""


####################################################################################################

class Tee:
    """
    A stream (cf. :py:mod:`libroll.streams`) that forwards all writes to a list of other streams
    (which can also be real file descriptors!).

    If the constructor is passed `close_on_exit=True`, the stream will attempt to close the
    underlying streams when closed, on a best-effort basis. Otherwise (the default), the underlying
    streams are left open.
    """

    def __init__(self, *files, close_on_exit=False):
        self.files = files
        self._closed = False

    def write(self, text):
        if self._closed:
            raise ValueError("I/O operation on closed stream.")
        for file in self.files:
            file.write(text)

    def flush(self):
        if self._closed:
            raise ValueError("I/O operation on closed stream.")
        for file in self.files:
            file.flush()

    def close(self):
        for file in self.files:
            try:
                file.close()
            except:
                pass  # best effort + streams might not support operation
        self._closed = True

    @property
    def closed(self):
        return self._closed

####################################################################################################
