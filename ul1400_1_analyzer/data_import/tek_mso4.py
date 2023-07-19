"""
Data import functionality for supported filetypes generated by the Tektronix MSO
4-series scope.

Module Attributes:
  FORMAT_TYPE_NAMES_CSV: The possible names that can be used as the format type
    to invoke the CSV importer.
  SOURCE_TYPE_NAMES: The possible names that can be used as the source type to
    invoke this data importer.
"""
from __future__ import annotations
import csv
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import os



SOURCE_TYPE_NAMES = [
    'tek_mso4',
]

FORMAT_TYPE_NAMES_CSV = [
    'csv',
]



def import_data(format_type:str, *args:Any, **kwargs:Any) -> Any:
    """
    Imports data for the specified format type using the configuration arguments
    provided.

    Args:
      format_type: The format type of the data being imported (e.g. 'csv').  See
        the relevant list of names defined at the top (`FORMAT_TYPE_NAMES_*`)
        for the intended format for a complete list of options.
      *args, **kwargs: The arguments to be passed along to the importer
        specified by the format type.  Will vary depending on the importer
        selected -- see the docstring for the targeted importer for full
        details.

    Returns:
      _: The data loaded by the importer.  Structure will depend upon the format
        type selected -- see the docstring for the targeted importer for full
        details.

    Raises:
      ValueError: Raised if an invalid format type is provided.
    """
    if format_type.lower() in FORMAT_TYPE_NAMES_CSV:
        return import_from_csv(*args, **kwargs)
    raise ValueError('Unsupported data importer format type for Tek MSO4:'
            f' {format_type}')



def import_from_csv(filepath:str|os.PathLike, by_labels:list[str]|None=None,
        by_ids:list[str]|None=None, case_sensitive:bool=False) \
        -> dict[str, dict[str, dict[float, float]]]:
    """
    Imports data from a CSV file generated by a Tektronix MSO 4-series
    oscilloscope.

    Args:
      filepath: The path to the file to load.  Can be a relative path.
      by_labels: The datasets to load by label name.  Can be used in combination
        with `by_ids`.
      by_ids: The datasets to load by id name (e.g. 'CH1', 'MATH1', etc.).  Can
        be used in combination with `by_labels`.
      case_sensitive: True if label and id names must match in a case sensitive
        fashion; False to match regardless of case.

    Returns:
      waveforms: The waveform data loaded for all specified datasets, keyed
        first by 'by_label' and 'by_id', then by the appropriate label or id
        name, where the resulting dict are the time-value points of the
        waveform.  If specified as case insensitive, label and id names will be
        lowercase.
    """
    if by_labels is None:
        by_labels = []
    if by_ids is None:
        by_ids = []
    if not case_sensitive:
        by_labels = [s.lower() for s in by_labels]
        by_ids = [s.lower() for s in by_ids]

    cols_by_label:dict[str, dict[str, int]] = {}
    cols_by_id:dict[str, dict[str, int]] = {}
    axis_start_cols:dict[str, list[int]] = {
        'label_row': [],
        'id_row': [],
    }
    waveforms:dict[str, dict[str, dict[float, float]]] = {
        'by_label': {s: {} for s in by_labels},
        'by_id': {s: {} for s in by_ids},
    }

    with open(filepath, newline='', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        data_row_parse_ready = False

        for row in reader:
            if not row:
                continue

            if data_row_parse_ready:
                _parse_csv_row_data(row, cols_by_label, cols_by_id, waveforms)

            elif row[0] == 'Labels':
                _parse_csv_row_labels(row, axis_start_cols, by_labels,
                        cols_by_label, case_sensitive)

            elif row[0] == 'TIME':
                _parse_csv_row_ids(row, axis_start_cols, by_ids, cols_by_id,
                        case_sensitive)

            if not data_row_parse_ready and axis_start_cols['label_row'] \
                    and axis_start_cols['id_row']:
                _validate_csv_headers(axis_start_cols, by_labels, cols_by_label,
                        by_ids, cols_by_id)
                data_row_parse_ready = True

    return waveforms



def _parse_csv_row_data(row:list[str], cols_by_label:dict[str, dict[str, int]],
        cols_by_id:dict[str, dict[str, int]],
        waveforms:dict[str, dict[str, dict[float, float]]]) -> None:
    """
    For the CSV format, parses a single data row.  It is the caller's
    responsibility to ensure the header rows have already been parsed.

    Args:
      row: The row of the CSV to parse.
      cols_by_label: The column numbers of the x and y data for each label that
        is to be loaded.  This is keyed by the label name (in lowercase if
        loaded without case sensitivity), then by "x" and "y" to get the 0-based
        column index of the x and y data values, respectively.
      cols_by_id: The column numbers of the x and y data for each ID that is to
        be loaded.  This is keyed by the ID name (in lowercase if loaded without
        case sensitivity), then by "x" and "y" to get the 0-based column index
        of the x and y data values, respectively.
      waveforms: The parsed waveform data to which this row of data will be
        added.  This is keyed first by 'by_label' and 'by_id', then by the
        appropriate label or id name, where the resulting dict are the
        time-value points of the waveform.  If importer was specified as case
        insensitive, label and id names will be lowercase.
    """
    for label, data in waveforms['by_label'].items():
        x = float(row[cols_by_label[label]['x']])
        y = float(row[cols_by_label[label]['y']])
        data[x] = y
    for id_, data in waveforms['by_id'].items():
        x = float(row[cols_by_id[id_]['x']])
        y = float(row[cols_by_id[id_]['y']])
        data[x] = y



def _parse_csv_row_labels(row:list[str], axis_start_cols:dict[str, list[int]],
        by_labels:list[str], cols_by_label:dict[str, dict[str, int]],
        case_sensitive:bool) -> None:
    """
    For the CSV format, parses the "label" header row.

    Args:
      row: The row of the CSV to parse.  It is the caller's responsibility to
        ensure this is the "label" header row.
      axis_start_cols: The column indices where each axis/data-group begins (
        i.e. data groups that share the same column for x-data).  This is keyed
        by "label_row" and "id_row", where the value of each is a list of the
        0-based column indices.  These lists are expected to match exactly.
      by_labels: The datasets to load by label name.  Only these label names
        will be loaded (with consideration of the case sensitivity provided).
      cols_by_label: The column numbers of the x and y data for each label that
        is to be loaded.  This will be updated with each label that is loaded.
        This is keyed by the label name (in lowercase if loaded without case
        sensitivity), then by "x" and "y" to get the 0-based column index of the
        x and y data values, respectively.
      case_sensitive: True if label names must match in a case sensitive
        fashion; False to match regardless of case.

    Raises:
      ValueError: Raised if a label is attempted to be loaded that has more than
        1 match (with consideration of the case sensitivity provided).
    """
    axis_start_cols['label_row'].append(0)
    if len(row) == 1:
        return

    previous_cell = row[0]
    for prev_index, cell in enumerate(row[1:]):
        col_index = prev_index + 1

        if not cell:
            previous_cell = ''
            continue

        if cell == 'Labels' and previous_cell == '':
            # There is a corner case where someone named a channel "Labels" and
            #   did not label the channel immediately previous to it in this
            #   group, but this is expected to be rare and will result in an
            #   exception when validating headers.  When using case
            #   insensitivity, this becomes impossible.
            axis_start_cols['label_row'].append(col_index)
            continue

        if not case_sensitive:
            cell = cell.lower()

        if cell in by_labels:
            if cell in cols_by_label:
                raise ValueError('Tek MSO4 CSV parser cannot support different'
                        f' channels with same label: {cell}')
            cols_by_label[cell] = {
                'x': axis_start_cols['label_row'][-1],
                'y': col_index,
            }



def _parse_csv_row_ids(row:list[str], axis_start_cols:dict[str, list[int]],
        by_ids:list[str], cols_by_id:dict[str, dict[str, int]],
        case_sensitive:bool) -> None:
    """
    For the CSV format, parses the "ID" header row (e.g. "CH1", "MATH1", etc.).

    Args:
      row: The row of the CSV to parse.  It is the caller's responsibility to
        ensure this is the "label" header row.
      axis_start_cols: The column indices where each axis/data-group begins (
        i.e. data groups that share the same column for x-data).  This is keyed
        by "label_row" and "id_row", where the value of each is a list of the
        0-based column indices.  These lists are expected to match exactly.
      by_ids: The datasets to load by ID name.  Only these ID names will be
        loaded (with consideration of the case sensitivity provided).
      cols_by_id: The column numbers of the x and y data for each ID that is to
        be loaded.  This will be updated with each ID that is loaded.  This is
        keyed by the ID name (in lowercase if loaded without case sensitivity),
        then by "x" and "y" to get the 0-based column index of the x and y data
        values, respectively.
      case_sensitive: True if ID names must match in a case sensitive fashion;
        False to match regardless of case.

    Raises:
      ValueError: Raised if an ID is attempted to be loaded that has more than 1
        match (with consideration of the case sensitivity provided).
    """
    axis_start_cols['id_row'].append(0)
    if len(row) == 1:
        return

    previous_cell = row[0]
    for prev_index, cell in enumerate(row[1:]):
        col_index = prev_index + 1

        if not cell:
            previous_cell = ''
            continue

        if cell == 'TIME' and previous_cell == '':
            axis_start_cols['id_row'].append(col_index)
            continue

        if not case_sensitive:
            cell = cell.lower()

        if cell in by_ids:
            if cell in cols_by_id:
                raise ValueError('Tek MSO4 CSV parser cannot support different'
                        f' channels with same ID: {cell}')
            cols_by_id[cell] = {
                'x': axis_start_cols['id_row'][-1],
                'y': col_index,
            }



def _validate_csv_headers(axis_start_cols:dict[str, list[int]],
        by_labels:list[str], cols_by_label:dict[str, dict[str, int]],
        by_ids:list[str], cols_by_id:dict[str, dict[str, int]]) -> None:
    """
    For the CSV format, validates the label and ID header columns to ensure they
    were loaded properly and completely.

    Args:
      axis_start_cols: The column indices where each axis/data-group begins (
        i.e. data groups that share the same column for x-data).  This is keyed
        by "label_row" and "id_row", where the value of each is a list of the
        0-based column indices.  These lists are expected to match exactly.
      by_labels: The datasets to load by label name.  Only these label names
        will be loaded (with consideration of the case sensitivity provided).
      cols_by_label: The column numbers of the x and y data for each label that
        is to be loaded.  This is keyed by the label name (in lowercase if
        loaded without case sensitivity), then by "x" and "y" to get the 0-based
        column index of the x and y data values, respectively.
      by_ids: The datasets to load by ID name.  Only these ID names will be
        loaded (with consideration of the case sensitivity provided).
      cols_by_id: The column numbers of the x and y data for each ID that is to
        be loaded.  This is keyed by the ID name (in lowercase if loaded without
        case sensitivity), then by "x" and "y" to get the 0-based column index
        of the x and y data values, respectively.

    Raises:
      ValueError: Raised if any of the following conditions are encountered:
        - No axis start column data is available (likely did not load header
              rows before calling, or CSV had no data).
        - The axis start column entries for the label row and the ID row do not
              match.
        - A requested label or ID was not found in the CSV.
    """
    if not axis_start_cols['label_row'] and not axis_start_cols['id_row']:
        raise ValueError('Cannot validate header rows if not already loaded')

    if axis_start_cols['label_row'] != axis_start_cols['id_row']:
        raise ValueError('Label and ID cols must have same axis start col'
                f' indices; found {axis_start_cols["label_row"]} for label row'
                f' and {axis_start_cols["label_row"]} for id row')
    missing_labels = set(by_labels) - set(cols_by_label.keys())
    if missing_labels:
        raise ValueError('Could not find all specified labels: '
                + ','.join([f'"{s}"' for s in sorted(missing_labels)]))
    missing_ids = set(by_ids) - set(cols_by_id.keys())
    if missing_ids:
        raise ValueError('Could not find all specified IDs: '
                + ','.join([f'"{s}"' for s in sorted(missing_ids)]))
