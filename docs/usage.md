# Usage

See [setup](setup.md) for required setup prior to first use.


## Executing
Main scripts intended for execution are in the root of `ul1400_1_analyzer`.
These need to be run from the repo root to make paths work correctly.

This project is developed with python 3.10, but it may work with earlier
versions at this time.

### Let-go Evaluation
This can be executed by providing the `letgo` sub-command when calling
`main.py`.  An example of running this from the repo root directory:

```
python ul1400_1_analyzer/main.py letgo -i tek_mso4 -f csv -d path/to/data.csv -c math1 -v ch1 -e dry -s 1e-6
```
where:
- `letgo` specifies that this performing the let-go evaluation
- `-i tek_mso4` specifies the data to import is sourced from the Tektronix MSO
      4-series
- `-f csv` specifies the data being imported is in CSV format
- `-d path/to/data.csv` is the relative or absolute file path to the source data
- `-c math1` is the identifier for the current data in that source data file
- `-v ch1` is the identifier for the voltage data in that source data file
- `-e dry` specifies to analyze the voltage data for dry conditions
- `-s 1e-6` specifies to only use data at the 1us time and later

See `python ul1400_1_analyzer/main.py letgo -h` for a full list of options.
