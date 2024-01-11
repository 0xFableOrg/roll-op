"""
This module enables extending existing exceptions with extra information.
"""


####################################################################################################

class ExtendedException(Exception):
    """
    A wrapper exception class that extends its inner exception with a prefix and a suffix to the
    message.
    """

    def __init__(self, e: Exception, prefix: str, suffix: str = ""):
        self.prefix = prefix
        self.suffix = suffix
        self.e = e

    def __getattr__(self, item: str):
        # forward all unknonw attributes & functions to the inner exception
        return getattr(self.e, item)

    def __str__(self):
        return f"(wrapping {type(self.e).__name__}):\n" \
               f"> {self.prefix}{self.e.__str__()}{self.suffix}"


####################################################################################################

def extend_exception(e: Exception, prefix: str, suffix: str = ""):
    """
    Extends the given exception with the given prefix and suffix added to the message, by wrapping
    it into a instance of :py:class:`ExtendedException`. These exceptions are not meant to be caught
    but to bubble up to the top level, where they will be printed.

    Note that to avoid "During handling of the above exception, another exception occurred" messages
    and double stack printing, you should use `raise lib.extend_exception(...) from None` to raise
    (the `from None` part suppresses the original exception).
    """
    return ExtendedException(e, prefix, suffix)

####################################################################################################
