"""
This modules contains classes defining "writeable streams", which implement the `write(text)` and
`flush()` methods, as well as `close()` and `closed` (though those do not seem required), making
them usable in place of file descriptors for functions such as subprocess.Popen, or assignable to
`sys.stdout`.
"""

####################################################################################################

import os


####################################################################################################

class WriteableStream:
    """
    Interface for writeable streams. Only the `write(text)` and `flush()` methods are required,
    and when extending this class, only `write(text)` needs to be overriden (`flush()` is a no-op by
    default).
    """

    def write(self, text):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass

    @property
    def closed(self) -> bool:
        return False


####################################################################################################

class Tee(WriteableStream):
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

class FileStream(WriteableStream):
    """
    A stream (cf. :py:mod:`libroll.streams`) that forwards all writes to a file.

    Compared to using a file descriptor, this stream ensures that the contents will be written to a
    file with the given path, even if the original file was deleted, moved, or even re-created.

    (However, this does not handle truncation — if the file is truncated, we will keep writing at
    the same offset a before, leading a file starting with a nul prelude.)

    If `truncate_on_reopen=True` (the default is `False`) is passed to the constructor, the file
    will be truncated when re-opened (which is relevant in case the old file was deleted or moved
    and a new file exists at the same path in its stead). Otherwise, we will append to it.
    """

    def __init__(self, path: str, truncate_on_reopen=False):
        self.path = path
        self.mode = "w" if truncate_on_reopen else "a"
        self.file = open(path, self.mode)
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
