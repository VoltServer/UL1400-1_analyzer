"""
Central entry point to import data from any supported source in any supported
format.

Module Attributes:
  SUPPORTED_FORMAT_TYPES: All possible format type names supported.  Not all
    format type are supported by all source types, but each format type will be
    supported by at least one.
  SUPPORTED_SOURCE_TYPES: All supported source type names.
  _SUPPORTED_IMPORTERS: All data import modules that are supported by this
    generic interface.
"""
from typing import Any

from ul1400_1_analyzer.data_import import tek_mso4



_SUPPORTED_IMPORTERS = [
    tek_mso4,
]

SUPPORTED_SOURCE_TYPES = {s for m in _SUPPORTED_IMPORTERS
        for s in m.SOURCE_TYPE_NAMES}

SUPPORTED_FORMAT_TYPES = {f for m in _SUPPORTED_IMPORTERS
        for f in m.FORMAT_TYPE_NAMES}



def import_data(source_type:str, format_type:str, *args:Any, **kwargs:Any) \
    -> Any:
    """
    Imports data from the specified source and format using the configuration
    arguments provided.

    Args:
      source_type: The importer source type (e.g. 'tek_mso4').  See the source
        type names defined at the top of each data importer for a complete list
        of options.
      format_type: The format type of the data being imported (e.g. 'csv').  See
        the relevant list of names defined at the top of the targeted source for
        the intended format for a complete list of options.
      *args, **kwargs: The arguments to be passed along to the importer
        specified by the source and format types.  Will vary depending on the
        importer selected -- see the docstring for the targeted importer for
        full details.

    Returns:
      _: The data loaded by the importer.  Structure will depend upon the source
        and format types selected -- see the docstring for the targeted importer
        for full details.

    Raises:
      ValueError: Raised if an invalid source type is provided.
    """
    if source_type.lower() in tek_mso4.SOURCE_TYPE_NAMES:
        return tek_mso4.import_data(format_type, *args, **kwargs)
    raise ValueError(f'Unsupported data importer source type: {source_type}')
