"""
This modules contains classes defining "streams", which implement the `write(text)` and `flush()`
methods, making them usable in place of file descriptors for functions such as subprocess.Popen, or
assignable to `sys.stdout`.
"""


####################################################################################################

class Tee:
    """
    A stream (cf. :py:mod:`libroll.streams`) that forwards all writes to a list of other streams
    (which can also be real file descriptors!).
    """

    def __init__(self, *files):
        self.files = files

    def write(self, text):
        for file in self.files:
            file.write(text)

    def flush(self):
        for file in self.files:
            file.flush()

####################################################################################################
