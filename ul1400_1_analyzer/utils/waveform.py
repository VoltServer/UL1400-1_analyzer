"""
This encapsulates waveform manipulations that facilitate analysis in a generic
fashion.

Module Attributes:
  N/A
"""
import copy
import itertools
from typing import Iterable



def merge_regions(regions:list[tuple[float, float]]) \
        -> list[tuple[float, float]]:
    """
    Merges all overlapped and exactly-adjacent regions in the list provided
    until there are no overlapping nor exactly-adjacent regions remaining.  An
    exactly-adjacent region is one where the start of one region and the end of
    the other is the same exact value.

    Args:
      regions: The regions to merge, where each entry is a start and end value
        pair.

    Returns:
      merged_regions: The regions represented by the ones provided, but with any
        overlapped or exactly-adjacent regions combined recursively into a
        single entry, where each entry is a start and end value pair.
    """
    merged_regions = copy.deepcopy(regions)
    regions_to_remove:Iterable[tuple[float, float]] = []
    need_another_iteration = True

    while need_another_iteration:
        need_another_iteration = False
        for region_pair in itertools.combinations(merged_regions, 2):
            union_region = unionize_regions(*region_pair)
            if union_region is not None:
                regions_to_remove = region_pair
                need_another_iteration = True
                break
        if need_another_iteration:
            for region in regions_to_remove:
                merged_regions.remove(region)
            merged_regions.append(union_region)

    return merged_regions



def expand_region(existing:tuple[float, float]|None,
        addition:tuple[float, float]) -> tuple[float, float]:
    """
    Expands the existing region to also include the additional region provided.
    If there is no existing region, the result will simply be the additional
    region.

    Args:
      existing: The existing region to expand.  Can be None if there is no
        existing region.
      addition: The additional region to add to the existing region.  Must be
        overlapped or exactly-adjacent.

    Returns:
      _: The union of the regions defined by the existing and addition regions,
        or simply the addition region if the existing region did not exist.

    Raises:
      ValueError: Raised when the existing and addition regions are provided and
        exist, but are not overlapped nor exactly-adjacent.
    """
    if existing is None:
        return addition

    union_region = unionize_regions(existing, addition)
    if union_region is None:
        raise ValueError('Cannot expand region if addition is not overlapped'
                ' nor exactly-adjacent')

    return union_region



def unionize_regions(region_1:tuple[float, float],
        region_2:tuple[float, float]) -> tuple[float, float]|None:
    """
    Finds the union of the 2 provided regions and returns the result if
    possible.

    Args:
      region_1: One of the regions to combine with union logic, where the values
        are a start and end value pair.
      region_2: One of the regions to combine with union logic, where the values
        are a start and end value pair.

    Returns:
      _: The new region that extends from the lowest start value of the 2
        regions to the highest end value of the 2 regions, provided that the
        combination of regions is continuous.  None if the 2 provided regions
        are neither overlapped nor exactly-adjacent.
    """
    if region_1[1] < region_2[0] or region_2[1] < region_1[0]:
        return None

    return (min(region_1[0], region_2[0]), max(region_1[1], region_2[1]))



def get_segment_from_waveform(waveform:dict[float, float]|None,
        start_time:float, end_time:float, min_duration:float,
        direction_to_extend_beyond:str) \
        -> dict[float, float]|None:
    """
    Gets a segment from a waveform based on the start and end times provided.  A
    minimum time window duration is enforced, where additional points are
    included from the direction indicated until the minimum duration is met.

    Scaling of units can be anything so long as they are consistent for all
    arguments and are expected in the return results.

    Args:
      waveform: The waveform data from which to extract a segment based on a
        specified time window.  Each entry is a point on the waveform, with the
        key being the time and the value being the value at that time.  Time
        value keys in the dictionary do not need to be ordered.
      start_time: The start time of the segment to extract, inclusive.
      end_time:  The end time of the segment to extract, inclusive
      min_duration: The minimum duration that must exist in the segment after
        extraction.  If this is not met, additional data will be included by
        exceeding either the start time specified or the end time specified
        based on the extension direction specified.
      direction_to_extend_beyond: The direction in which to progress to include
        additional data if the minimum duration is not met.  For example, if the
        minimum duration is not met and this is specified as "start", then this
        will include data below the start time provided.  Valid values are
        "start" and "end".

    Returns:
      _: The segment of the waveform that includes the data at least from the
        start time to the end time, with additional data included in the
        direction specified until the minimum duration is met.  None if no
        waveform provided or there is insufficient data in the waveform to meet
        the minimum duration based on the specified parameters.
    """
    if waveform is None:
        return None

    segment = {t: v for t, v in waveform.items() if start_time <= t <= end_time}

    try:
        while max(segment.keys()) - min(segment.keys()) < min_duration:
            if direction_to_extend_beyond == 'start':
                next_earlier_time = max({t: v for t, v in waveform.items()
                        if t < min(segment.keys())}.keys())
                segment[next_earlier_time] = waveform[next_earlier_time]
            elif direction_to_extend_beyond == 'end':
                next_later_time = min({t: v for t, v in waveform.items()
                        if t > max(segment.keys())}.keys())
                segment[next_later_time] = waveform[next_later_time]
    except ValueError:
        return None

    return segment
