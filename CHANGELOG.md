# Change log
All notable changes to this project will be documented in this file.  This
should be succinct, but still capture "what I would want co-developers to know".

This project adheres to [Semantic Versioning](http://semver.org/), but reserves
the right to do whatever the hell it wants with pre-release versioning.

Observe format below, particularly:
- version headings (with links)
- diff quick link(s) under each version heading
- project section (dir) sub-headings for each version, alphabetical with
      `Project & Toolchain` at top, then all sub-packages/modules, then docs.
- type-of-change prefix for each change line
- each change only a line or 2, maybe 3 (sub-lists allowed in select cases)
- issue (not PR) link for every change line
- milestones, projects, issues, and PRs with issue linkage for each version in
      alphanumeric order
- reference-style links at very bottom of file, grouped and in completion order
- 'Unit Tests' sections only updated when async change with relevant src change
  - Otherwise assumed src changes have corresponding unit test changes

Release change log convention via
[Keep a Changelog](http://keepachangelog.com/).


---


# [Unreleased](https://github.com/VoltServer/UL1400-1_analyzer/tree/develop)

Compare to [stable](https://github.com/VoltServer/UL1400-1_analyzer/compare/stable...develop)


### Project & Toolchain: `.git*`, `.editorconfig`
- [Added] `.editorconfig` and `.gitattributes` added ([#1][]).
- [Added] VS Code related items added to `.gitignore` ([#1][]).
- [Added] `*.csv` added to `.gitignore` [#7][].


### Project & Toolchain: CircleCI
- [Added] CircleCI implemented, with `.circleci/config.yml` file that ensures
      project builds successfully ([#1][]).
- [Added] `mypy` type hint checker added for ensuring type hints fully done and
      correct for app ([#1][]).


### Project & Toolchain: CI Support
- [Added] `dir_init_checker.py` added to new `ci_support` dir to run code for
      checking `__init__.py` files are up to date ([#1][]).
- [Added] `version_checker.py` added to verify that the version format conforms
      to standard practice based on branch ([#1][]).


### Project & Toolchain: Conventions
- [Added] Units omitted from names and assumed to be base standard units unless
      otherwise specified (in which case, it should be added to name) ([#1][]).
- [Added] Loggers can use f-strings with caution ([#1][]).
- [Added] Versioning guidelines added ([#1][]).


### Project & Toolchain: Package, Requirements
- [Added] `requirements.txt` added, with `pylint` and `mypy` as only entries
      ([#1][]).
- [Added] `alive-progress` added to `requirements.txt` ([#4][]).


### Project & Toolchain: Pylint, Mypy
- [Added] `.pylintrc` added to configure pylint, with source code paths added
      ([#1][]).
- [Added] `.mypy.ini` added to configure `mypy` execution for app code and test
      code ([#1][]).
- [Added] `max-locals` set to `20` ([#4][]).
- [Changed] `max-locals` increased from `20` to `25` to balance out the
      `max-args` being increased from `10` to `15` ([#5][], [#6][]).


### Analysis: Analyzer Support
- [Added] `analyzer_support.py` added for shared data and functionality among
      analyzers, which for now is `Interpretation` and `StandardVersion` enums
      with defaults defined ([#5][], [#6][]).


### Analysis: Letgo Analyzer
- [Added] `letgo_analyzer.py` added with ability to analyze waveforms strictly
      to UL1400-1 with parallel CPU core processing support ([#4][]).
- [Added] Audit function added to check if the configuration used is critically
      valid for UL1400-1 assessment ([#5][], [#6][]).
- [Changed] Current and voltage let-go assessments now performed with the
      interpretation level and standard version factored in ([#5][], [#6][]).


### Data Import: Data Importer
- [Added] `data_importer.py` added with generic function call for
      `import_data()` meant to be central point for all imports ([#7][]).
- [Added] Module attributes added to list all supported source types and format
      types for usage in CLI help messages ([#4][]).


### Data Import: Tek MSO4
- [Added] `tek_mso4.py` added with support for CSV parsing for Tektronix MSO
      4-series scopes ([#7][]).
- [Added] Module attributes added to list all supported format types for usage
      in CLI help messages ([#4][]).


## Utils: CLI:
- [Added] `cli.py` added for CLI processing support, with case-insensitive enum
      option parsing implemented ([#5][], [#6][]).


## Utils: Waveform
- [Added] `waveform.py` added to encapsulate generic waveform manipulations,
      such as extracting segments and merging regions ([#4][]).


### Main
- [Added] `main.py` added with CLI sub-parser for letgo and help function to
      route CLI args to letgo analyzer as well as display results ([#4][]).
- [Added] Support for interpretation level and standard version CLI args added
      along with the usage and audit for those parameters ([#5][], [#6][]).


### Version
(This does not need to note every version change, but can if issue tied to it.)
- [Added] `version.py` added, with initial dev version set and methods to build
      a full build version str including git status items ([#1][]).


### Docs: CHANGELOG
- [Added] This `CHANGELOG.md` file created and updated with all project work
      to-date ([#1][]).


### Docs: CONTRIBUTING
- [Added] `CONTRIBUTING.md` added to project root, covering dev setup, general
      workflow, and conventions ([#1][]).
- [Added] Added convention that exceptions will be raised if an unsupported
      interpretation or standard version encountered in a function that uses
      that configuration ([#5][], [#6][]).

### Docs: README
- [Changed] Updated with project intro (mostly placeholder), links, CI badge
      ([#1][]).


### Docs: Setup
- [Added] `setup.md` added with install requirements ([#1][]).


### Docs: Usage
- [Added] `usage.md` added with bare minimum on how to run ([#1][]).
- [Added] Example of executing let-go evaluation added ([#4][]).


### Ref Links

#### Milestones & Projects

#### Issues
- [#1][]
- [#4][]
- [#5][]
- [#6][]
- [#7][]

#### PRs
- [#2][] for [#1][]
- [#8][] for [#7][]
- [#9][] for [#4][]
- [#10][] for [#5][], [#6][]

---


Reference-style links here (see below, only in source) in develop-merge order.

[#1]: https://github.com/VoltServer/UL1400-1_analyzer/issues/1 'Issue #1'
[#7]: https://github.com/VoltServer/UL1400-1_analyzer/issues/7 'Issue #7'
[#4]: https://github.com/VoltServer/UL1400-1_analyzer/issues/4 'Issue #4'
[#5]: https://github.com/VoltServer/UL1400-1_analyzer/issues/5 'Issue #5'
[#6]: https://github.com/VoltServer/UL1400-1_analyzer/issues/6 'Issue #6'

[#2]: https://github.com/VoltServer/UL1400-1_analyzer/pull/2 'PR #2'
[#8]: https://github.com/VoltServer/UL1400-1_analyzer/pull/8 'PR #8'
[#9]: https://github.com/VoltServer/UL1400-1_analyzer/pull/9 'PR #9'
[#10]: https://github.com/VoltServer/UL1400-1_analyzer/pull/10 'PR #10'
