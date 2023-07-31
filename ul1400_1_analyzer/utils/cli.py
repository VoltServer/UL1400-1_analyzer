"""
Includes support for Command Line Interface tools.

Module Attributes:
  N/A
"""
import argparse
from enum import Enum
from typing import Any



class CaseInsensitiveChoices(list):
    """
    A helper class for "choice" options when adding arguments for argparse
    parsers, this facilitates comparing choice options in a case-insensitive
    fashion while not losing the case information of the user's input.

    This does require the expected choice options to be upper-case.
    """
    def __contains__(self, other:object) -> bool:
        """
        Checks if the other element (regardless of case) is contained in this
        list.

        Args:
          other: The item to check if it is contained in this list.

        Returns:
          _: True if item is contained in the list, regardless of case; False
            otherwise.

        Raises:
          TypeError: Raised if a non-string item is passed in as the other
            element to check if it is contained in this list.
        """
        if not isinstance(other, str):
            raise TypeError('Only string types supported')
        return super().__contains__(other.upper())



class EnumByNameAction(argparse.Action):
    """
    A helper class for the "action" to take when adding arguments to argparse
    parsers, this allows CLI input to be compared against enum member names in
    a case-insensitive fashion while still supporting the display of choices if
    an invalid input is entered (or help is requested).

    This does force the display of choice options to be the enum member names in
    upper case.

    Instance Attributes:
      _enum_type: The Enum that was defined as the type by the argparse parser
        option.
    """
    def __init__(self, option_strings:Any, dest:Any, nargs:Any=None,
            **kwargs:Any) -> None:
        """
        Creates the action, ensuring that the proper inputs have been provided
        by the argparse parser.

        Args:
          option_strings: The option strings allowed for this argument.  Not
            relevant for positional arguments.
          dest: The destination variable name.
          nargs: The number of args configuration for the parser argument.  This
            is expected to be None (i.e. omitted when adding the argument).
          **kwargs: The other keyword arguments.  It is required that 'type` be
            one of the keys, where the value is expected to be an Enum subclass.

        Raises:
          TypeError: Raised if no 'type' is provided.
          ValueError: Raised if nargs used (which is not supported), or the
            'type' is defined as a non-Enum class.
        """
        if nargs is not None:
            raise ValueError("nargs not allowed")

        enum_type = kwargs.pop('type', None)
        if enum_type is None:
            raise ValueError('`type` must be provided to argument kwargs')
        if not issubclass(enum_type, Enum):
            raise TypeError('Only enum types supported')

        kwargs.setdefault('choices', CaseInsensitiveChoices(
                [e.name.upper() for e in enum_type]))

        super().__init__(option_strings, dest, **kwargs)

        self._enum_type = enum_type



    def __call__(self, parser:argparse.ArgumentParser,
            namespace:argparse.Namespace, values:Any,
            option_string:str|None=None) -> None:
        """
        Parses the command line string received for this argument option.  With
        a valid string passed to `values`, this will set the destination
        variable to the parsed enum member.

        Args:
          parser: The ArgumentParser object which contains this action.
          namespace: The Namespace object that will be returned by parse_args().
            Most actions add an attribute to this object using setattr().
          values: The associated command-line arguments, with any type
            conversions applied.  Type conversions are specified with the type
            keyword argument to add_argument().
          option_string: The option string that was used to invoke this action.
            The option_string argument is optional, and will be absent if the
            action is associated with a positional argument.

        Raises:
          ValueError: Raised if the values received cannot be parsed as a valid
            enum member.
        """
        value = None
        for member in self._enum_type:
            if values.upper() == member.name.upper():
                value = member
        if value is None:
            raise ValueError(f'Invalid value for {self._enum_type.__name__}'
                    f' enum: {values}')
        setattr(namespace, self.dest, value)
