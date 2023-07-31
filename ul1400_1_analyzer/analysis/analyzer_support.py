"""
This encapsulates any generic supporting elements that may be required by more
than 1 analyzer module.

Module Attributes:
  DEFAULT_INTERPRETATION: The default interpretation level to be used by this
    project.
  DEFAULT_STANDARD_VERSION: The default version of the standard to be used by
    this project.
  LATEST_STANDARD_VERSION: The latest released version of the standard.
"""
from __future__ import annotations
from enum import Enum



class Interpretation(Enum):
    """
    These are the "levels" of how the standard should be interpreted, ranging
    from a strict adherence to everything exactly as it is written to
    speculative attempts to resolve ambiguous, conflicting, or absent material.
    Higher levels should be used with increased caution, as they are at greater
    risk of not being the official final interpretation per the standards body.
    """
    STRICT = 'Level 0: This only allows interpretations strictly adhering to' \
            ' the exact language in the standard.'
    TYPOS = 'Level 1: This allows provable typos in the standard to be fixed' \
            ' and used in the analysis.'
    REASONABLE = 'Level 2: This allows ambiguous, conflicting, or absent' \
            ' material from the standard to be resolved where a reasonably' \
            ' confident interpretation is possible.  This should be something' \
            ' where arguments can be constructed based on other parts of the' \
            ' the standard or the referenced literature.  This also' \
            ' incorporates previous levels where possible.'
    SPECULATIVE = 'Level 3: This allows for experimental and other wildly' \
            ' speculative interpretations to be explored as solutions to' \
            ' ambiguous, conflicting, or absent material that cannot' \
            ' otherwise be proven with reasonable confidence.  This also' \
            ' incorporates previous levels where possible.'



class StandardVersion(Enum):
    """
    The supported versions of the standard that can be analyzed against.
    """
    UL1400_1_ISSUE_1 = 'UL1400-1, Issue Number 1; December 19, 2022'



DEFAULT_INTERPRETATION = Interpretation.STRICT

LATEST_STANDARD_VERSION = StandardVersion.UL1400_1_ISSUE_1
DEFAULT_STANDARD_VERSION = LATEST_STANDARD_VERSION
