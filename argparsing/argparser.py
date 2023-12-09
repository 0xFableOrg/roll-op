import argparse
from dataclasses import dataclass, field

from .newline_formatter import NewlineFormatter


####################################################################################################

@dataclass
class Argument:
    name: str
    help: str
    action: str = "store"
    dest: str | None = None
    kwargs: dict[str, str] = field(default_factory=dict)


class CommandListItem:
    pass


@dataclass
class Delimiter(CommandListItem):
    name: str


@dataclass
class Command(CommandListItem):
    """
    Description of a program command.
    """
    name: str
    help: str
    description: str | None = None
    args: list[Argument] = field(default_factory=list)

    def arg(self, name: str, help: str,
            action: str = "store",
            dest: str | None = None,
            **kwargs):
        """
        Adds an argument that is specific to a command.

        See here for the documentation of the arguments of this method:
        https://docs.python.org/3/library/argparse.html#quick-links-for-add-argument
        """
        self.args.append(Argument(
            name=name, help=help, action=action, dest=dest, kwargs=kwargs))


####################################################################################################

class Argparser:
    """
    Convenient logic around the argparse library so we can get the flexibility & UX we need.

    We add the possibility to separated commands ("subparsers") with delimiter, and the possibility
    to define "global" arguments that can appear both before or after a command.

    The parser automatically gets a -h/--help option that shows the help for the program or for a
    command if present.
    """

    # ----------------------------------------------------------------------------------------------

    def __init__(self, program_name: str, description: str):
        self.program_name = program_name
        self.description = description
        self.parser = None
        self.subparsers = None
        self.parent_command_parser = None
        self.command_parsers = {}
        self.command_list_items = []
        self.global_args = []

    # ----------------------------------------------------------------------------------------------

    def delimiter(self, name: str):
        """
        Adds a section delimiter to group multiple subparsers together.
        """
        self.command_list_items.append(Delimiter(name))

    # ----------------------------------------------------------------------------------------------

    def command(self, name: str, help: str, description: str | None = None) -> Command:
        """
        Adds a command to the parser.
        """
        command = Command(name=name, help=help, description=description)
        self.command_list_items.append(command)
        return command

    # ----------------------------------------------------------------------------------------------

    def arg(self, name: str, help: str,
            action: str = "store",
            dest: str | None = None,
            **kwargs):
        """
        Adds a global argument, that can appear both before or after a command.

        See here for the documentation of the arguments of this method:
        https://docs.python.org/3/library/argparse.html#quick-links-for-add-argument
        """
        self.global_args.append(Argument(
            name=name, help=help, action=action, dest=dest, kwargs=kwargs))

    # ----------------------------------------------------------------------------------------------

    def parse(self) -> argparse.Namespace:
        """
        Returns the result of parsing the program's arguments.
        """
        self._build_parser()
        namespace = self.parser.parse_args()
        ns = namespace.__dict__

        for arg in self.global_args:
            dest = self._get_dest(arg)
            cmd_dst = dest + "_command"
            if arg.action == "store_true":
                ns[dest] = ns[dest] or ns[cmd_dst]
            elif arg.action == "store_false":
                ns[dest] = ns[dest] and ns[cmd_dst]
            elif arg.action == "store" or arg.action == "store_const":
                # last value takes precedence
                ns[dest] = ns[cmd_dst] or ns[dest]
            elif arg.action == "append" or arg.action == "append_const":
                ns[dest].extend(ns[cmd_dst])
            elif arg.action == "count":
                ns[dest] = ns[dest] + ns[cmd_dst]
            elif arg.action == "extend":
                ns[dest].extend(ns[cmd_dst])
            del ns[cmd_dst]

        return namespace

    # ----------------------------------------------------------------------------------------------

    def print_help(self, command: str | None = None):
        """
        Prints the help for the program (no command specified) or for a specific command.
        """
        self._build_parser()
        if command is None:
            self.parser.print_help()
        else:
            self.command_parsers[command].print_help()

    # ----------------------------------------------------------------------------------------------

    def _build_parser(self):
        if self.parser is not None:
            return

        self.parser = argparse.ArgumentParser(
            prog=self.program_name,
            description=self.description,
            formatter_class=NewlineFormatter,
            allow_abbrev=False,
            add_help=False)

        self.parser.add_argument(
            # Suppressed via `add_help=False` but reintroduced here, undocumented.
            "-h", "--help",
            help=argparse.SUPPRESS,
            default=False,
            action="store_true",
            dest="show_help")

        self.parent_command_parser = argparse.ArgumentParser(add_help=False)

        self.subparsers = self.parser.add_subparsers(
            title="commands",
            dest="command",
            metavar="<command>")

        for item in self.command_list_items:
            if isinstance(item, Command):
                self._add_command(item)
                for arg in item.args:
                    self._add_command_arg(item, arg)
            elif isinstance(item, Delimiter):
                self._add_delimiter(item)

        # must come after adding the commands
        for arg in self.global_args:
            self._add_global_arg(arg)

    # ----------------------------------------------------------------------------------------------

    def _add_command(self, command: Command):
        description = command.description or command.help
        parser = self.subparsers.add_parser(
            command.name,
            help=command.help,
            description=description)
        self.command_parsers[command.name] = parser

    # ----------------------------------------------------------------------------------------------

    def _add_delimiter(self, delimiter: Delimiter):
        formatted = f"\n    -- {delimiter.name} --\n"
        self.subparsers.add_parser(formatted, help="")
        # Don't show the delimiter in the error messages when providing an invalid subcommand.
        del self.subparsers.choices[formatted]

    # ----------------------------------------------------------------------------------------------

    @staticmethod
    def _add_arg(parser: argparse.ArgumentParser, arg: Argument):
        parser.add_argument(
            arg.name,
            help=arg.help,
            action=arg.action,
            dest=arg.dest,
            **arg.kwargs)

    # ----------------------------------------------------------------------------------------------

    @staticmethod
    def _get_dest(arg: Argument) -> str:
        if arg.dest:
            return arg.dest
        return arg.name.removeprefix("--").removeprefix("-")

    # ----------------------------------------------------------------------------------------------

    def _add_global_arg(self, arg: Argument):
        self._add_arg(self.parser, arg)

        dest = self._get_dest(arg) + "_command"
        command_arg = Argument(
            name=arg.name, help=arg.help, action=arg.action, dest=dest, kwargs=arg.kwargs)

        for item in self.command_list_items:
            if isinstance(item, Command):
                self._add_command_arg(item, command_arg)

    # ----------------------------------------------------------------------------------------------

    def _add_command_arg(self, command: Command, arg: Argument):
        self._add_arg(self.command_parsers[command.name], arg)


####################################################################################################
