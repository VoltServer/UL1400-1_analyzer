"""
This performs the evaluation of the let-go limit and the Fault Recovery Period
per UL1400-1.

Module Attributes:
  _PROGRESS_COUNTER: A shared multiprocessing value that tracks the progress of
    how many iterations have been completed across all processes.  Will be None
    when not in use.
"""
import math
import multiprocessing as mp
import os
from typing import Any

from alive_progress import alive_bar                      # type: ignore[import]

from ul1400_1_analyzer.analysis import analyzer_support
from ul1400_1_analyzer.analysis.analyzer_support \
        import Interpretation, StandardVersion
from ul1400_1_analyzer.utils import waveform as waveform_utils



_PROGRESS_COUNTER = None



def _init_shared_data(shared_data:Any) -> None:
    """
    Initializes any data that is to be shared across processes when using
    multiprocessing.

    This is intended to be called at the start of each process.

    Args:
      shared_data: The data that is to be shared.  At this time, this is a tuple
        that only includes the reference to the global progress counter (which
        must be created prior to this call).
    """
    global _PROGRESS_COUNTER                  # pylint: disable=global-statement
    _PROGRESS_COUNTER = shared_data



def audit_config_valid(interpretation:Interpretation|None,
        standard_version:StandardVersion, min_window_duration:float|None=None,
        **_kwargs:Any) -> None:
    """
    Audits the configuration parameters to confirm they are valid to critically
    assess to the standard.

    Will provide a warning message if there is a possibility that results could
    mislead towards a false positive on compliance.

    Args:
      interpretation: The level of how strictly to interpret the standard.
      standard_version: The version of the standard to use for analysis.
      min_window_duration [s]: The minimum time duration to use as a window
        size for evaluating data.  For compliance, this should likely be the
        minimum Fault Recovery Period duration required by UL1400-1.
      **_kwargs: Absorbs any extra keywords arguments that may be passed in.
        Not used.

    Raises:
      ValueError: Raised if an unsupported interpretation or standard version
        was provided.
    """
    if standard_version \
            is not StandardVersion.UL1400_1_ISSUE_1:
        raise ValueError('Only Standard Version UL1400-1 Issue #1 is supported'
                ' at this time')
    if interpretation not in [Interpretation.STRICT, Interpretation.TYPOS,
            Interpretation.REASONABLE, Interpretation.SPECULATIVE]:
        raise ValueError(f'Unsupported interpretation: {interpretation}')

    if min_window_duration < 3:
        print('**WARNING** Window duration is too small to correctly assess the'
                ' Fault Recovery Period for UL1400-1 Issue #1')



def find_time_regions_below_letgo(current_waveform:dict[float, float]|None=None,
        voltage_waveform:dict[float, float]|None=None,
        env_conditions:str|None=None, start_time:float|None=None,
        min_window_duration:float=3, num_cores:int|None=None,
        interpretation:Interpretation=analyzer_support.DEFAULT_INTERPRETATION,
        standard_version:StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION) \
        -> tuple[tuple[float, float], ...]:
    """
    Finds the time regions that are below the let-go threshold.  When the
    appropriate minimum recovery duration is provided, this can be used to
    identify regions that may qualify as Fault Recovery Periods per UL1400-1.

    Args:
      current_waveform [s, A]: The fault current waveform to evaluate if it is
        below let-go.  Each entry is a point on the waveform, with the key being
        the time and the value being the electrical current value.  This can be
        omitted if only the fault voltage waveform will be used, but this does
        potentially produce excessively conservative results.  The time values
        do not need to align with the voltage waveform time values to be valid.
        Time value keys in the dictionary do not need to be ordered.
      voltage_waveform [s, V]: The fault voltage waveform to evaluate if it is
        below let-go.  Each entry is a point on the waveform, with the key being
        the time and the value being the electrical voltage value.  This can be
        omitted if only the fault current waveform will be used, but this does
        potentially produce excessively conservative results.  The time values
        do not need to align with the current waveform time values to be valid.
        Time value keys in the dictionary do not need to be ordered.  If this is
        used, the environmental conditions must be provided.
      env_conditions: The environmental conditions to be used for evaluating
        let-go.  This is only required if the fault voltage waveform is
        provided, as this is the only waveform to which it applies.  The valid
        values are "wet" and "dry".
      start_time [s]: The time above which to analyze waveform data.  This is
        useful if the fault is introduced at some mid-point in the time series
        and may contain invalid data earlier than that.  This can be omitted to
        use all data in the waveforms.
      min_window_duration [s]: The minimum time duration to use as a window
        size for evaluating data.  For compliance, this should likely be the
        minimum Fault Recovery Period duration required by UL1400-1.
      num_cores: The number of cores to use.  Can be omitted to use all cores.
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.

    Returns:
      time_regions_below_letgo [s]: These are the time regions identified as
        being below the let-go threshold per the data and parameters specified.
        It REQUIRES the correct parameters to be specified (e.g.
        min_window_duration) in order for this to suggest the analysis is
        compliant with UL1400-1.  Each entry in the list is a pair of start and
        end time values that each identify the continuous region where the
        waveforms are below let-go for all time windows of min_window_duration
        or larger.  An empty list indicates no regions were identified to be
        below the let-go threshold per the data and parameters specified.
    """
    both_waveforms = {
        'current': current_waveform,
        'voltage': voltage_waveform,
    }
    time_regions_below_letgo:list[tuple[float, float]] = []

    if num_cores is None:
        num_cores = os.cpu_count()
    num_processes = min(num_cores, os.cpu_count())

    last_error_message = None
    def _error_handler(ex:Exception) -> None:
        """
        Internal error handler for processes in the multiprocessing pool.

        Args:
          ex: The exception encountered in the process.
        """
        nonlocal last_error_message
        last_error_message = str(ex)


    for measurement_type, waveform in both_waveforms.items():
        if waveform is None:
            continue

        min_start_time = start_time if start_time is not None else min(
                waveform.keys())
        target_times = [(t - min_window_duration, t) for t in waveform.keys()
                if t - min_window_duration >= min_start_time]

        global _PROGRESS_COUNTER              # pylint: disable=global-statement
        _PROGRESS_COUNTER = mp.Value('i', 0)

        with mp.Pool(num_processes, initializer=_init_shared_data,
                initargs=(_PROGRESS_COUNTER, )) as pool:
            with alive_bar(len(target_times),
                    title=f'Analyzing {measurement_type} waveform') \
                    as progress_bar:

                args = [(measurement_type, waveform, *t, min_window_duration,
                            env_conditions, interpretation, standard_version)
                            for t in target_times]
                future_result = pool.starmap_async(_analyze_segment, args,
                        error_callback=_error_handler)

                while not future_result.ready():
                    if _PROGRESS_COUNTER.value != 0:
                        with _PROGRESS_COUNTER.get_lock():
                            increment = _PROGRESS_COUNTER.value
                            _PROGRESS_COUNTER.value = 0
                        progress_bar(increment)   # pylint: disable=not-callable

                if not future_result.successful():
                    print(last_error_message)
                else:
                    time_regions_below_letgo.extend(
                            [r for r in future_result.get() if r is not None])

                pool.close()
                pool.join()

        _PROGRESS_COUNTER = None

    print('Merging results...')
    return waveform_utils.merge_regions(time_regions_below_letgo)



def _analyze_segment(measurement_type:str, waveform:dict[float, float]|None,
        target_start_time:float, target_end_time:float,
        min_window_duration:float, env_conditions:str|None,
        interpretation:Interpretation=analyzer_support.DEFAULT_INTERPRETATION,
        standard_version:StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION) \
        -> tuple[float, float]|None:
    """
    Finds the segment of data to analyze and performs the let-go analysis.

    This is intended to be run on a separate process/thread for parallel
    computing, but it is not required.

    Args:
      measurement_type: The type of measurement represented in the segment data
        provided.  Valid values are "current" and "voltage".
      waveform: The current or voltage waveform data from which to extract a
        segment based on a specified time window.  Each entry is a point on the
        waveform, with the key being the time and the value being the value at
        that time.  Time value keys in the dictionary do not need to be ordered.
      target_start_time: The start time of the segment to extract, inclusive.
        This is an ideal target start time; depending on the data in the
        waveform and the other constraints, this may not be the exact start time
        used.  This value may be exceeded by a lower value if additional data is
        needed to meet the minimum window duration.
      target_end_time: The end time of the segment to extract, inclusive.  This
        is an ideal target end time; depending on the data in the waveform and
        the other constraints, this may not be the exact end time used.  This
        value may not be present in the data at all, and it certainly will not
        be exceeded.
      min_window_duration [s]: The minimum time duration to use as a window
        size for evaluating data.  For compliance, this should likely be the
        minimum Fault Recovery Period duration required by UL1400-1.
      env_conditions: The environmental conditions to be used for evaluating
        let-go.  This is only required if the fault voltage waveform is
        provided, as this is the only waveform to which it applies.  The valid
        values are "wet" and "dry".
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.

    Returns:
      new_passing_region: The new region, defined as a start and end time, that
        passes the let-go threshold.  If test failed, this will be None.
    """
    new_passing_region = None
    segment = waveform_utils.get_segment_from_waveform(waveform,
            target_start_time, target_end_time, min_window_duration,
            'start')

    if is_below_letgo(measurement_type, segment.values(),
            env_conditions, interpretation, standard_version):
        new_passing_region = (min(segment.keys()), max(segment.keys()))

    if _PROGRESS_COUNTER is not None:
        with _PROGRESS_COUNTER.get_lock():
            _PROGRESS_COUNTER.value += 1

    return new_passing_region



def is_below_letgo(measurement_type:str, segment_values:list[float]|None,
        env_conditions:str|None=None,
        interpretation:Interpretation=analyzer_support.DEFAULT_INTERPRETATION,
        standard_version:StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION) -> bool|None:
    """
    Determines if the provided segment of data is below the let-go threshold.
    When the appropriate data is provided, this can be used to assess if the
    segment may qualify as a Fault Recovery Period per UL1400-1.

    Args:
      measurement_type: The type of measurement represented in the segment data
        provided.  Valid values are "current" and "voltage".
      segment_values: The values of the segment of the waveform to evaluate (
        i.e. times associated with each value are not needed and should not be
        included).
      env_conditions: The environmental conditions to be used for evaluating
        let-go.  This is only required if the measurement type provided is
        "voltage", as this is the only type to which it applies.  The valid
        values are "wet" and "dry".
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.

    Returns:
      _: True if the segment is below the appropriate let-go threshold based on
        the provided arguments; False if segment data exists and provably
        exceeded the let-go threshold; None if no segment data provided and
        therefore could not asses.

    Raise:
      ValueError: Raised if an invalid value for the measurement type is
        provided.
    """
    if measurement_type == 'current':
        return is_current_below_letgo(segment_values, interpretation,
                standard_version)
    if measurement_type == 'voltage':
        return is_voltage_below_letgo(segment_values, env_conditions,
                interpretation, standard_version)
    raise ValueError('Measurement type must be "voltage" or "current", got'
            f' "{measurement_type}"')



def is_current_below_letgo(segment_values:list[float]|None,
        interpretation:Interpretation=analyzer_support.DEFAULT_INTERPRETATION,
        standard_version:StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION) -> bool|None:
    """
    Determines if the provided segment of data is below the let-go threshold for
    current.  When the appropriate data is provided, this can be used to assess
    if the segment may qualify as a Fault Recovery Period per UL1400-1.

    Args:
      segment_values: The electrical current values of the segment of the
        waveform to evaluate (i.e. times associated with each value are not
        needed and should not be included).
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.

    Returns:
      _: True if the segment is below the appropriate let-go threshold based on
        the provided arguments; False if segment data exists and provably
        exceeded the let-go threshold; None if no segment data provided and
        therefore could not asses.

    Raise:
      ValueError: Raised if an ambiguous condition with respect to UL1400-1 is
        encountered and could not be resolved; or if an unsupported
        interpretation or standard version was provided.
    """
    if segment_values is None:
        return None

    if standard_version \
            is not StandardVersion.UL1400_1_ISSUE_1:
        raise ValueError('Only Standard Version UL1400-1 Issue #1 is supported'
                ' at this time')
    if interpretation not in [Interpretation.STRICT, Interpretation.TYPOS,
            Interpretation.REASONABLE, Interpretation.SPECULATIVE]:
        raise ValueError(f'Unsupported interpretation: {interpretation}')

    a_to_ma_scalar = 1000

    peak_ma = max(segment_values) * a_to_ma_scalar
    mean_ma = sum(segment_values) / len(segment_values) * a_to_ma_scalar

    if interpretation in [Interpretation.REASONABLE,
            Interpretation.SPECULATIVE]:
        # Based on source of these limits from "Effect of Wave Form on Let-Go
        #   Currents" by Charles F. Dalziel [December 1943], it could be argued
        #   that the mean is concerned with the magnitude (i.e. absolute value),
        #   while the peak is the magnitude (i.e. absolute value) of the largest
        #   deviation from the zero point.
        peak_ma = max([abs(x) for x in segment_values]) * a_to_ma_scalar
        mean_ma = abs(mean_ma)

    if mean_ma < 0:
        # This should likely invert or consider worst peak, but technically is
        #   undefined.  See reasonable interpretation for possible handling
        raise ValueError('DC values less than 0 are not supported for let-go:'
                f' {mean_ma} mA')

    if mean_ma <= 4.21:
        limit_ma = 5 * math.sqrt(2)

    elif mean_ma <= 30:
        if interpretation is Interpretation.STRICT:
            limit_ma = 33.3 + 0.89 * mean_ma
        else:
            # Via figure 5.4 in UL1400-1 Issue #1, it is easy to confirm that
            #   33.3 is a typo of 3.33
            limit_ma = 3.33 + 0.89 * mean_ma

    else:
        # This should likely be a failure, but technically is undefined
        if interpretation in [Interpretation.STRICT, Interpretation.TYPOS]:
            raise ValueError('DC values greater than 30 mA are not supported'
                    f' for let-go: {mean_ma} mA')
        return False

    return peak_ma <= limit_ma



def is_voltage_below_letgo(segment_values:list[float]|None,
        env_conditions:str,
        interpretation:Interpretation=analyzer_support.DEFAULT_INTERPRETATION,
        standard_version:StandardVersion=
            analyzer_support.DEFAULT_STANDARD_VERSION) -> bool|None:
    # pylint: disable=too-many-branches
    """
    Determines if the provided segment of data is below the let-go threshold for
    voltage.  When the appropriate data is provided, this can be used to assess
    if the segment may qualify as a Fault Recovery Period per UL1400-1.

    Args:
      segment_values: The electrical voltage values of the segment of the
        waveform to evaluate (i.e. times associated with each value are not
        needed and should not be included).
      env_conditions: The environmental conditions to be used for evaluating
        let-go.  This is only required if the measurement type provided is
        "voltage", as this is the only type to which it applies.  The valid
        values are "wet" and "dry".
      interpretation: The level of how strictly to interpret the standard.  Can
        be omitted to use default.
      standard_version: The version of the standard to use for analysis.  Can be
        omitted to use default.

    Returns:
      _: True if the segment is below the appropriate let-go threshold based on
        the provided arguments; False if segment data exists and provably
        exceeded the let-go threshold; None if no segment data provided and
        therefore could not asses.

    Raise:
      ValueError: Raised if an ambiguous condition with respect to UL1400-1 is
        encountered and could not be resolved; or if an invalid value for the
        environmental condition is provided; or if an unsupported interpretation
        or standard version was provided.
    """
    if segment_values is None:
        return None

    if standard_version \
            is not StandardVersion.UL1400_1_ISSUE_1:
        raise ValueError('Only Standard Version UL1400-1 Issue #1 is supported'
                ' at this time')
    if interpretation not in [Interpretation.STRICT, Interpretation.TYPOS,
            Interpretation.REASONABLE, Interpretation.SPECULATIVE]:
        raise ValueError(f'Unsupported interpretation: {interpretation}')

    if env_conditions not in ['wet', 'dry']:
        raise ValueError('Environmental conditions must be specified as wet or'
                f' dry; got {env_conditions}')

    peak = max(segment_values)
    mean = sum(segment_values) / len(segment_values)

    if interpretation in [Interpretation.REASONABLE,
            Interpretation.SPECULATIVE]:
        # Based on source of these limits from "Effect of Wave Form on Let-Go
        #   Currents" by Charles F. Dalziel [December 1943], it could be argued
        #   that the mean is concerned with the magnitude (i.e. absolute value),
        #   while the peak is the magnitude (i.e. absolute value) of the largest
        #   deviation from the zero point.
        peak = max([abs(x) for x in segment_values])
        mean = abs(mean)

    if mean < 0:
        # This should likely invert or consider worst peak, but technically is
        #   undefined
        raise ValueError('DC values less than 0 are not supported for let-go:'
                f' {mean} V')

    if env_conditions == 'wet':
        if mean <= 10.4:
            limit = 21.2
        elif mean <= 30:
            limit = 16.5 + 0.45 * mean
        else:
            # This should likely be a failure, but technically is undefined
            if interpretation in [Interpretation.STRICT, Interpretation.TYPOS]:
                raise ValueError('DC values greater than 30 V are not supported'
                        f' for let-go under wet conditions: {mean} V')
            return False

    elif env_conditions == 'dry':
        if mean <= 20.9:
            limit = 42.4
        elif mean <= 60:
            limit = 33 + 0.45 * mean
        else:
            # This should likely be a failure, but technically is undefined
            if interpretation in [Interpretation.STRICT, Interpretation.TYPOS]:
                raise ValueError('DC values greater than 60 V are not supported'
                        f' for let-go under dry conditions: {mean} V')
            return False

    return peak <= limit
