"""
This performs the evaluation of the let-go limit and the Fault Recovery Period
per UL1400-1.

Module Attributes:
  N/A
"""
import math

from ul1400_1_analyzer.utils import waveform as waveform_utils



def find_time_regions_below_letgo(current_waveform:dict[float, float]|None=None,
        voltage_waveform:dict[float, float]|None=None,
        env_conditions:str|None=None, start_time:float|None=None,
        min_window_duration:float=3) -> tuple[tuple[float, float], ...]:
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

    for measurement_type, waveform in both_waveforms.items():
        if waveform is None:
            continue

        working_region = None
        min_start_time = start_time if start_time is not None else min(
                waveform.keys())
        target_end_time = max(waveform.keys())
        target_start_time:float|None = target_end_time - min_window_duration

        while target_start_time is not None \
                and target_start_time >= min_start_time:
            segment = waveform_utils.get_segment_from_waveform(waveform,
                    target_start_time, target_end_time, min_window_duration,
                    'start')

            if is_below_letgo(measurement_type, segment.values(),
                    env_conditions):
                new_region = (min(segment.keys(), max(segment.keys())))
                working_region = waveform_utils.expand_region(working_region,
                        new_region)
            elif working_region is not None:
                time_regions_below_letgo.append(working_region)
                working_region = None

            remaining_end_times = [t for t in waveform.keys()
                    if t < target_end_time]
            if remaining_end_times:
                target_end_time = max(remaining_end_times)
                target_start_time = target_end_time - min_window_duration
            else:
                target_start_time = None

        if working_region is not None:
            time_regions_below_letgo.append(working_region)

    return waveform_utils.merge_regions(time_regions_below_letgo)



def is_below_letgo(measurement_type:str, segment_values:list[float]|None,
        env_conditions:str|None=None) -> bool|None:
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
        return is_current_below_letgo(segment_values)
    if measurement_type == 'voltage':
        return is_voltage_below_letgo(segment_values, env_conditions)
    raise ValueError('Measurement type must be "voltage" or "current", got'
            f' "{measurement_type}"')



def is_current_below_letgo(segment_values:list[float]|None) -> bool|None:
    """
    Determines if the provided segment of data is below the let-go threshold for
    current.  When the appropriate data is provided, this can be used to assess
    if the segment may qualify as a Fault Recovery Period per UL1400-1.

    Args:
      segment_values: The electrical current values of the segment of the
        waveform to evaluate (i.e. times associated with each value are not
        needed and should not be included).

    Returns:
      _: True if the segment is below the appropriate let-go threshold based on
        the provided arguments; False if segment data exists and provably
        exceeded the let-go threshold; None if no segment data provided and
        therefore could not asses.

    Raise:
      ValueError: Raised if an ambiguous condition with respect to UL1400-1 is
        encountered and could not be resolved.
    """
    if segment_values is None:
        return None

    a_to_ma_scalar = 1000

    peak_ma = max(segment_values) * a_to_ma_scalar
    mean_ma = sum(segment_values) / len(segment_values) * a_to_ma_scalar

    if mean_ma < 0:
        # This should likely invert or consider worst peak, but technically is
        #   undefined
        raise ValueError('DC values less than 0 are not supported for let-go:'
                f' {mean_ma} mA')
    if mean_ma <= 4.21:
        limit_ma = 5 * math.sqrt(2)
    elif mean_ma <= 30:
        # NOTE: Technically this is 33.3, not 3.33; but it is easy to determine
        #   that 33.3 is a typo
        limit_ma = 3.33 + 0.89 * mean_ma
    else:
        # This should likely be a failure, but technically is undefined
        raise ValueError('DC values greater than 30 mA are not supported for'
                f' let-go: {mean_ma} mA')

    return peak_ma <= limit_ma



def is_voltage_below_letgo(segment_values:list[float]|None,
        env_conditions:str) -> bool|None:
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

    Returns:
      _: True if the segment is below the appropriate let-go threshold based on
        the provided arguments; False if segment data exists and provably
        exceeded the let-go threshold; None if no segment data provided and
        therefore could not asses.

    Raise:
      ValueError: Raised if an ambiguous condition with respect to UL1400-1 is
        encountered and could not be resolved; or if an invalid value for the
        environmental condition is provided.
    """
    if segment_values is None:
        return None

    if env_conditions not in ['wet', 'dry']:
        raise ValueError('Environmental conditions must be specified as wet or'
                f' dry; got {env_conditions}')

    peak = max(segment_values)
    mean = sum(segment_values) / len(segment_values)

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
            raise ValueError('DC values greater than 30 V are not supported for'
                    f' let-go under wet conditions: {mean} V')
    elif env_conditions == 'dry':
        if mean <= 20.9:
            limit = 42.4
        elif mean <= 60:
            limit = 33 + 0.45 * mean
        else:
            # This should likely be a failure, but technically is undefined
            raise ValueError('DC values greater than 60 V are not supported for'
                    f' let-go under dry conditions: {mean} V')

    return peak <= limit
