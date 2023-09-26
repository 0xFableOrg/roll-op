"""
Utilities to extend argparse.
"""

import argparse


####################################################################################################

class SmartFormatter(argparse.HelpFormatter):
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


####################################################################################################

def add_subparser(
        subparsers, name: str, help: str, description: str | None = None) \
        -> argparse.ArgumentParser:
    """
    Helper function for adding a subparser with a description derived from the help.
    """
    description = help if description is None else description
    return subparsers.add_parser(
        name,
        help=help,
        description=description)


####################################################################################################

def add_subparser_delimiter(subparsers, name: str):
    """
    Adds a section delimiter to group multiple subparsers together.
    """
    formatted = f"\n    -- {name} --\n"
    parser = subparsers.add_parser(formatted, help="")

    # Don't show the delimiter in the error messages when providing an invalid subcommand.
    del subparsers.choices[formatted]

    return parser


####################################################################################################
