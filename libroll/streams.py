"""
This modules contains classes defining "writeable streams", which implement the `write(text)` and
`flush()` methods, as well as `close()` and `closed` (though those do not seem required), making
them usable in place of file descriptors for functions such as subprocess.Popen, or assignable to
`sys.stdout`.
"""

####################################################################################################

import os


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
            except:  # noqa: E722
                pass  # best effort + streams might not support operation
        self._closed = True

    @property
    def closed(self):
        return self._closed


####################################################################################################

class FileStream:
    """
    A stream (cf. :py:mod:`libroll.streams`) that forwards all writes to a file.

    Compared to using a file descriptor, this stream ensures that the file exists before writing,
    re-creating it if it was deleted.

    If a mode is passed to the constructor (either "a" or "w" for append or truncate, with "a" being
    the default), it will be used each time the file is re-created.
    """

    def __init__(self, path: str, mode: str = "a"):
        self.path = path
        self.mode = mode
        self.file = open(path, mode)
        self._closed = False

    def _connected_to_file(self):
        # check if the file descriptor is still connected to a file on disk
        return os.fstat(self.file.fileno()).st_nlink > 0

    def write(self, s):
        if self._closed:
            raise ValueError("I/O operation on closed stream.")

        if not self._connected_to_file():
            self.file.close()
            self.file = open(self.path, "a")

        self.file.write(s)

    def flush(self):
        if self._closed:
            raise ValueError("I/O operation on closed stream.")

        if not self.file.closed:
            self.file.flush()

    def close(self):
        self._closed = True
        self.file.close()

    @property
    def closed(self):
        return self._closed

####################################################################################################
