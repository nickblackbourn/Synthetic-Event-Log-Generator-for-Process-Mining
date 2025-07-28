# Synthetic Event Log Generator

This tool generates synthetic event logs for process mining and process intelligence use cases. It supports configurable process activities, deviations, case/event attributes, and process variants.

## Features
- **Configurable number of cases**
- **Precise deviation frequencies** (per-case probability)
- **Support for case and event attributes**
- **Process variants with frequency control**
- **Balance between strict variant order and process realism**
- **CSV output for easy analysis**

## Requirements
- Python 3.7+
- [pm4py](https://pypi.org/project/pm4py/)
- pandas

Install dependencies with:
```bash
pip install pm4py pandas
```

## Usage

### 1. Install dependencies

```
pip install pandas pm4py
```

### 2. Prepare your variables file

Edit `variables.txt` to define your process, deviations, attributes, and variants. Example:

```
Context:
Order-to-Cash process for B2B sales

Activities:
Receive Order
Check Credit
Approve Order
Pick Items
Pack Items
Ship Order
Send Invoice
Receive Payment

Deviations:
# You can specify where the deviation should occur using | before=<activity/sequence> or | after=<activity/sequence>
# Only one placement modifier ('before' or 'after') is allowed per deviation.
# For sequences, use comma-separated activities (no spaces).
# Examples:
# Late Payment: 0.15 | after=Send Invoice
# Order Change: 0.10 | before=Pick Items
# Partial Shipment: 0.05 | after=Approve Order,Pick Items
Late Payment: 0.15 | after=Send Invoice
Order Change: 0.10 | before=Pick Items
Partial Shipment: 0.05 | after=Approve Order,Pick Items

CaseAttributes:
CustomerType: New, Returning, VIP
Region: North, South, East, West

EventAttributes:
Resource: Alice, Bob, Carol, Dave
Channel: Email, Phone, Web

Variants:
Standard: Receive Order, Check Credit, Approve Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.7
No Credit Check: Receive Order, Approve Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.2
Express: Receive Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.1
```

### 3. Run the generator

```
python generate_synthetic_event_log.py --variables-file variables.txt --output-file synthetic_event_log.csv --n-cases 1000 --random-seed 42 --shuffle-fraction 0.2 --deviation-at-end --max-activities 10
```

#### Key CLI options for realism and strictness
- `--shuffle-fraction`: Fraction of cases to shuffle activities for realism (default: 0.2). Set to 0 for strict variant order.
- `--deviation-at-end`: If set, deviations are always inserted at the end of the activity sequence (preserves variant order).
- `--random-seed`: Set for reproducible results.
- `--max-activities`: Maximum number of activities per case (default: 8).

**Tip:**
- For strict conformance to variants, use `--shuffle-fraction 0 --deviation-at-end`.
- For more realistic, noisy logs, increase `--shuffle-fraction` and omit `--deviation-at-end`.

### 4. Output

The generated CSV will contain one row per event, with columns for case name, activity, timestamp, and all configured attributes.

## Advanced Configuration
- **Deviations**: Each deviation is inserted in the exact percentage of cases specified.
- **Variants**: Frequencies should sum to 1.0. Cases are distributed accordingly.
- **Attributes**: Add as many case/event attributes as needed; values are randomly assigned.

## Example Output
| case:concept:name | Activity      | Timestamp           | CustomerType | Region | Resource | Channel |
|-------------------|--------------|---------------------|--------------|--------|----------|---------|
| Case_1            | Receive Order| 2025-07-27 10:00:00 | VIP          | North  | Alice    | Email   |
| Case_1            | Check Credit | 2025-07-27 10:10:00 | VIP          | North  | Bob      | Phone   |
| ...               | ...          | ...                 | ...          | ...    | ...      | ...     |

## License
MIT License

## Author
Your Name
