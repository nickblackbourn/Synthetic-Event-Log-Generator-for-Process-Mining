# Synthetic Event Log Generator for Process Mining

This tool generates a synthetic event log suitable for process mining using the [PM4PY](https://pm4py.fit.fraunhofer.de/) Python package. The generated log can be used for research, teaching, or testing process mining algorithms.

## Features
- Reads process context, activities, and deviations from a text file (`variables.txt`).
- Generates a synthetic event log with columns: `UID`, `Activity`, `Timestamp`.
- Supports random deviations and activity order shuffling for realistic traces.
- Outputs a CSV file (`synthetic_event_log.csv`) and can be converted to a PM4PY event log object.

## Requirements
- Python 3.7+
- [pm4py](https://pypi.org/project/pm4py/)
- pandas

Install dependencies with:
```bash
pip install pm4py pandas
```

## Usage
1. **Prepare `variables.txt`** in the same folder, with the following structure:
   ```
   Context:
   context_var1
   context_var2
   Activities:
   Activity A
   Activity B
   Activity C
   Deviations:
   Deviation X
   Deviation Y
   ```
2. **Run the script:**
   ```bash
   python generate_synthetic_event_log.py
   ```
3. **Output:**
   - `synthetic_event_log.csv` — the generated event log.

## File Descriptions
- `generate_synthetic_event_log.py` — Main script to generate the event log.
- `variables.txt` — Input file specifying context, activities, and deviations.
- `synthetic_event_log.csv` — Output event log in CSV format.

## Customization
- Change the number of cases or activities by editing the parameters in `generate_event_log()`.
- Modify the structure of `variables.txt` to suit your process.

## License
MIT License

## Author
Your Name
