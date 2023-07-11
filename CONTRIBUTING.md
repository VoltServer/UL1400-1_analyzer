# Contributing

Guidelines for contributing are largely TBD.  Helpful items for setup and usage,
including for forking, are below.

Follow existing conventions as best as possible.

Respect the CI and the CI will respect you.

- [Usage](#usage)
- [Conventions](#conventions)
- [One-time Setup](#one-time-setup)



# Usage

## Workflows
Before pushing, it is recommended to run through the checks that CircleCI will
run.  In short, this is largely running from the repo root:
```
python -m pylint ul1400_1_analyzer
python -m pylint ci_support

python -m mypy ul1400_1_analyzer

python ci_support/dir_init_checker.py ul1400_1_analyzer
python ci_support/dir_init_checker.py ci_support

python ci_support/version_checker.py dev-required
```

When running `mypy`, it may be useful to do a final check with the
`--no-incremental` CLI arg just to ensure it is not passing due to an improper
cache.  This is especially at risk if the `.mypy.ini` file has been changed or
CLI args have changed.

The `version_checker.py` could be run with different args, but during
development, it is most likely that `dev-required` is the correct arg.



# Conventions

## Logger
Balancing readability against performance, the pylint warnings
`logging-fstring-interpolation` and `logging-not-lazy` are disabled.  The
intention is largely for this to apply to warnings and more severe log levels
as well as anything that would be low overhead.  It is recommended that anything
info or debug level, especially if there are many calls or each call is an
time-expensive interpolation to use the
`logger.debug('log %(name)s', {'name'=name_var})` sort of methods instead so
that the interpolation is only executed when that logger level is enabled.


## Units of measure
Units of measure are assumed to be the standard metric unit of measure
appropriate for that item with no scaling.  For example, capacitance is expected
to be in Farads (i.e. not nanofarads), and distance is expected to be in meters.

When naming variables and functions, any unit related items should typically be
omitted.  The only exception should be when there is a need to specify in a
different unit or scaling (e.g. getting user input in nanofarads, or working
with distance in feet).


## Versioning
See the top of `/ul1400_1_analyzer/version.py` for information on the version
information.  The general idea is that development versions must have a `+dev`
appended while stable branch commits must not have this.  `release/*` branches
are where this is allowed to be either to allow for the transition.



# One-time Setup

## CircleCI
If forking this project, CircleCI will need contexts setup.  See
`.circleci/config.yml` for the contexts needed; the contents should be mostly
obvious (e.g. `docker-hub-creds` is intended to define the user/pass env vars).
For the Docker Hub password, an access token should be created on the Security
page of your Docker Hub account profile.
