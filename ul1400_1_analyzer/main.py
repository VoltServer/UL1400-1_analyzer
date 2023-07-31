"""
Main entry point for all analysis.

Module Attributes:
  N/A
"""
from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any

from ul1400_1_analyzer.analysis import analyzer_support
from ul1400_1_analyzer.analysis import letgo_analyzer
from ul1400_1_analyzer.analysis.analyzer_support \
        import Interpretation, StandardVersion
from ul1400_1_analyzer.data_import import data_importer
from ul1400_1_analyzer.utils import cli

if TYPE_CHECKING:
    import os



def main_letgo(format_type:str, importer_type:str,
        current_waveform_id:str|None=None,
        data_source_file:str|os.PathLike|None=None,
        env_conditions:str|None=None, start_time:float|None=None,
        voltage_waveform_id:str|None=None, window_duration:float|None=None,
        interpretation:analyzer_support.Interpretation=
            analyzer_support.DEFAULT_INTERPRETATION,
        num_cores:int|None=None,
        standard_version:analyzer_support.StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION, **_kwargs:Any) -> None:
    """
    The main entry point for let-go evaluation, this processes the CLI input
    arguments to pass along for analysis.

    Args:
      format_type: The format type of the data being imported (e.g. 'csv').  See
        the relevant list of names defined at the top of the targeted importer
        source for the intended format for a complete list of options.
      importer_type: The importer source type (e.g. 'tek_mso4').  See the source
        type names defined at the top of each data importer for a complete list
        of options.
      current_waveform_id: The identifier for the current waveform in the data
        being imported.  Usage depends on the importer and format type.  Can be
        omitted if current waveform is not being analyzed.
      data_source_file: The path to the file that as the source data to import.
        Can be a relative or absolute path.  Can be omitted if not relevant for
        the selected importer and format type.
      env_conditions: The environmental conditions to be used for evaluating
        let-go.  This is only required if the fault voltage waveform is
        provided, as this is the only waveform to which it applies.  The valid
        values are "wet" and "dry".
      start_time [s]:
      voltage_waveform_id: The identifier for the voltage waveform in the data
        being imported.  Usage depends on the importer and format type.  Can be
        omitted if voltage waveform is not being analyzed.
      window_duration [s]: The minimum time duration to use as a window
        size for evaluating data.  For compliance, this should likely be the
        minimum Fault Recovery Period duration required by UL1400-1.
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      num_cores: The number of CPU cores to use for parallel processing.  Can be
        omitted to use all cores.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.
      **_kwargs: Absorbs any extra keywords arguments that may be passed in.
        Not used.
    """
    by_ids = []
    if current_waveform_id:
        by_ids.append(current_waveform_id)
    if voltage_waveform_id:
        by_ids.append(voltage_waveform_id)

    data = data_importer.import_data(importer_type, format_type,
            filepath=data_source_file, by_ids= by_ids)

    analyzer_kwargs = {}
    if current_waveform_id:
        analyzer_kwargs['current_waveform'] \
                = data['by_id'][current_waveform_id]
    if voltage_waveform_id:
        analyzer_kwargs['voltage_waveform'] \
                = data['by_id'][voltage_waveform_id]
    if env_conditions:
        analyzer_kwargs['env_conditions'] = env_conditions
    if start_time:
        analyzer_kwargs['start_time'] = start_time
    if window_duration:
        analyzer_kwargs['min_window_duration'] = window_duration
    if num_cores:
        analyzer_kwargs['num_cores'] = num_cores
    analyzer_kwargs['interpretation'] = interpretation
    analyzer_kwargs['standard_version'] = standard_version

    passing_regions = letgo_analyzer.find_time_regions_below_letgo(
            **analyzer_kwargs)
    if not passing_regions:
        print('No regions comply with let-go limits')
    else:
        print('The following regions comply with let-go limits based on'
                ' provided parameters:')
        for index, region in enumerate(passing_regions):
            print(f' {index + 1}: {region[0]*1000:.3f} ms'
                    f' - {region[1]*1000:.3f} ms')

    letgo_analyzer.audit_config_valid(**analyzer_kwargs)





if __name__ == '__main__':
    main_parser = argparse.ArgumentParser(
            description='The main entry point for any analysis to do per'
                ' UL1400-1.  See sub-commands for further usage information.')
    subparsers = main_parser.add_subparsers(
            description='A sub-command must be provided in order to select'
                ' which type of analysis to perform.',
            help='Sub-command options for type of analysis to perform.')

    letgo_parser = subparsers.add_parser('letgo',
            description='Performs analysis with respect to let-go.',
            help='Performs analysis with respect to let-go.', )
    letgo_parser.add_argument('-c', '--current-waveform-id',
            help='The identifier for the current waveform data to use from the'
                ' provided raw data source file.  Can be omitted if current'
                ' waveform analysis is being skipped.')
    letgo_parser.add_argument('-d', '--data-source-file',
            help='The raw data source file to analyze.  Can be a relative or'
                ' absolute file path.')
    letgo_parser.add_argument('-e', '--env-conditions',
            choices=['dry', 'wet'],
            help='The environmental conditions under which to perform the'
                ' analysis.  This is only relevant for voltage waveforms, so'
                ' this can be omitted if the voltage waveform is omitted; and'
                ' it is required if the voltage waveform is provided.')
    letgo_parser.add_argument('-f', '--format-type',
            required=True,
            choices=sorted(data_importer.SUPPORTED_FORMAT_TYPES),
            help='The format type of the raw data source file being imported.'
                '  Not all choices will be supported by all importer types.')
    letgo_parser.add_argument('-i', '--importer-type',
            required=True,
            choices=sorted(data_importer.SUPPORTED_SOURCE_TYPES),
            help='The type of importer to use for parsing the raw data source'
                ' file.')
    letgo_parser.add_argument('-s', '--start-time',
            type=float,
            help='The earliest time to include in the analysis from the current'
                ' and voltage waveforms.  This is useful to exclude earlier'
                ' times where the fault had not yet been introduced and'
                ' therefore are not relevant/valid for analysis.  Can be'
                ' omitted to analyze the entire waveform.')
    letgo_parser.add_argument('-v', '--voltage-waveform-id',
            help='The identifier for the voltage waveform data to use from the'
                ' provided raw data source file.  Can be omitted if voltage'
                ' waveform analysis is being skipped.')
    letgo_parser.add_argument('-w', '--window-duration',
            type=float,
            help='The window duration to use as a sliding window to analyze'
                ' data.  For UL1400-1, this likely should be the Fault Recovery'
                ' Period, in which case this can be omitted since that is'
                ' the default.  If provided, this must be a time in seconds.'
                '  This will ensure at least this much time is in the window'
                ' for each analysis window.')
    letgo_parser.add_argument('--interpretation-level',
            dest='interpretation',
            action=cli.EnumByNameAction,
            type=Interpretation,
            default=analyzer_support.DEFAULT_INTERPRETATION,
            help='The level of interpretation to use when performing the'
                ' evaluation.  This can range from a strict interpretation of'
                ' the standard to more speculative interpretations to resolve'
                ' ambiguous, conflicting, or absent material.  Defaults to'
                ' strict.')
    letgo_parser.add_argument('--num-cores',
            help='The number of CPU cores to use during the analysis.  Can be'
                ' omitted, at which point it will default to all cores.  Note'
                ' that using all cores may make the computer slow/unresponsive'
                ' until analysis is complete; but the progress indicator should'
                ' continue showing that it is actively running.')
    letgo_parser.add_argument('--standard_version',
            action=cli.EnumByNameAction,
            type=StandardVersion,
            default=analyzer_support.DEFAULT_STANDARD_VERSION,
            help='The version of the standard to use when performing the'
                ' evaluation.  Defaults to the latest.')
    letgo_parser.set_defaults(func=main_letgo)

    cli_args = main_parser.parse_args()
    cli_args.func(**vars(cli_args))
