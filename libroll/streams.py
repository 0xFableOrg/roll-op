"""
This modules contains classes defining "writeable streams", which implement the `write(text)` and
`flush()` methods, as well as `close()` and `closed` (though those do not seem required), making
them usable in place of file descriptors for functions such as subprocess.Popen, or assignable to
`sys.stdout`.
"""


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

    Compared to using a file descriptor, this stream reopens the file every time it is written to.
    This ensures that the contents will always be appended at the end of the file currently at the
    given path, even if the original file was deleted, moved, re-created, or truncated.

    (It is possible to detect deletion pretty easily, but not moves and truncation, which require
    multiple system calls.)
    """

    def __init__(self, path: str):
        self.path = path
        self._closed = False

    def write(self, s):
        if self._closed:
            raise ValueError("I/O operation on closed stream.")

        with (open(self.path, "a")) as f:
            f.write(s)

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed


####################################################################################################
