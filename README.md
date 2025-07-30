
# Synthetic Event Log Generator

This tool generates synthetic event logs for process mining and process intelligence use cases. It is fully YAML-driven, supports strict business-rule-compliant process variants and deviations, and allows attribute-based assignment for both variants and deviations.

## Features
- **YAML configuration** for all process logic, variants, deviations, durations, and attributes
- **Attribute-based assignment**: Link variants and deviations to specific case attributes (e.g., CustomerType, Region)
- **Multi-step deviations**: Deviations can be a sequence of activities
- **Strict conformance**: No legacy or unreachable code; all logic is YAML-driven
- **Precise deviation and variant frequencies** (per-case probability/frequency)
- **Support for case and event attributes**
- **Activity and deviation durations** (affecting timestamps)
- **CSV output for easy analysis**

## Requirements
- Python 3.7+
- [pm4py](https://pypi.org/project/pm4py/)
- pandas
- pyyaml

Install dependencies with:
```bash
pip install pm4py pandas pyyaml
```

## Usage

### 1. Prepare your YAML configuration

Edit `variables.txt` to define your process, deviations, attributes, and variants. Example:

```yaml
context: Order-to-Cash process for B2B sales

activities:
  - Receive Order
  - Check Credit
  - Approve Order
  - Order Change Requested
  - Order Change Approved
  - Re-pick Items
  - Re-pack Items
  - Pick Items
  - Pack Items
  - Partial Shipment
  - Notify Customer
  - Backorder Created
  - Ship Backorder
  - Ship Order
  - Send Invoice
  - Payment Reminder Sent
  - Late Payment
  - Apply Late Fee
  - Receive Payment
  - Complaint Received
  - Return Processed
  - Refund Issued
  - VIP Approval
  - Gift Packaging
  - Credit Check Escalated
  - Manual Review
  - Order Cancellation
  - Express Handling
  - Priority Picking
  - Priority Packing

activity_durations:
  Default: 1440
  Receive Order: 60
  Check Credit: 240
  # ...

case_attributes:
  CustomerType: [New, Returning, VIP]
  Region: [North, South, East, West]

event_attributes:
  Resource: [Alice, Bob, Carol, Dave]
  Channel: [Email, Phone, Web]

variants:
  - name: Standard
    sequence: [Receive Order, Check Credit, Approve Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment]
    frequency: 0.6
  - name: VIP
    sequence: [Receive Order, Check Credit, Approve Order, VIP Approval, Gift Packaging, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment]
    frequency: 0.1
    attributes:
      CustomerType: VIP
  # ...

deviations:
  - name: Late Payment
    probability: 0.15
    after: Send Invoice
    steps: [Payment Reminder Sent, Late Payment, Apply Late Fee]
    description: Customer pays invoice late
    attributes:
      CustomerType: New
      Region: East
  # ...
```

### 2. Run the generator

```bash
python generate_synthetic_event_log.py --variables-file variables.txt --output-file synthetic_event_log.csv --n-cases 1000 --random-seed 42 --max-activities 20
```

#### Key CLI options
- `--variables-file`: Path to YAML configuration (default: variables.txt)
- `--output-file`: Output CSV file (default: synthetic_event_log.csv)
- `--n-cases`: Number of cases to generate (default: 100)
- `--random-seed`: Set for reproducible results
- `--max-activities`: Maximum number of activities per case (default: 8)

### 3. Validate and analyze the output

Use the unified QA script to check conformance, ratios, and summary:

```bash
python qa_event_log.py --all
```
Or run individual checks:
```bash
python qa_event_log.py --strict
python qa_event_log.py --summary
python qa_event_log.py --ratios
```

### 4. Output

The generated CSV will contain one row per event, with columns for case name, activity, timestamp, and all configured attributes.

## Advanced Configuration
- **Attribute-based assignment**: Use the `attributes` field in variants or deviations to restrict them to specific case attribute values.
- **Multi-step deviations**: Use the `steps` field to insert a sequence of activities for a deviation.
- **Strict placement**: Deviations are only inserted if the placement rule matches the variant path; otherwise, a warning is logged and the deviation is skipped.
- **Timestamps and durations**: Each activity (including deviation steps) gets its own duration and timestamp, reflecting the true process flow and impact of deviations.
- **Variants**: Frequencies should sum to 1.0. Cases are distributed accordingly.
- **Attributes**: Add as many case/event attributes as needed; values are randomly assigned unless restricted by a variant or deviation.

## Example Output
| case:concept:name | Activity                | Timestamp           | CustomerType | Region | Resource | Channel |
|-------------------|-------------------------|---------------------|--------------|--------|----------|---------|
| Case_1            | Receive Order           | 2025-07-27 10:00:00 | VIP          | North  | Alice    | Email   |
| Case_1            | Check Credit            | 2025-07-27 10:10:00 | VIP          | North  | Bob      | Phone   |
| Case_1            | Approve Order           | 2025-07-27 10:20:00 | VIP          | North  | Carol    | Web     |
| Case_1            | Order Change Requested  | 2025-07-27 10:25:00 | VIP          | North  | Dave     | Email   |
| ...               | ...                     | ...                 | ...          | ...    | ...      | ...     |

## License
MIT License

## Author
Your Name
