import argparse


class NewlineFormatter(argparse.HelpFormatter):
    """
    This formatter helps us force newlines in the help text, whenever prefixed with "R|".
    Adapted from: https://stackoverflow.com/a/22157136 and https://stackoverflow.com/a/32974697
    """

    # Works for subparser & argument help text.
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        # this is the RawTextHelpFormatter._split_lines
        # noinspection PyProtectedMember
        return argparse.HelpFormatter._split_lines(self, text, width)

    # Works for the description.
    # noinspection PyProtectedMember
    def _fill_text(self, text, width, indent):
        if text.startswith('R|'):
            return text[2:]
        return super()._fill_text(text, width, indent)
