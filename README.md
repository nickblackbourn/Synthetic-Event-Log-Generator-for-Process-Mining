# Synthetic Event Log Generator


This tool generates synthetic event logs for process mining and process intelligence use cases. It supports configurable process activities, multi-step deviations, case/event attributes, and process variants. You can control the realism and strictness of the generated log, and model both standard and exceptional process flows.


## Features
- **Configurable number of cases**
- **Multi-step deviations** (deviations can be a sequence of activities, not just a single event)
- **Precise deviation frequencies** (per-case probability)
- **Strict deviation placement** (deviations are only inserted at the configured position if possible)
- **Support for case and event attributes**
- **Process variants with frequency control**
- **Activity and deviation durations** (affecting timestamps)
- **Noise/realism control** (`--shuffle-fraction`)
- **Strict conformance option** (`--shuffle-fraction 0` for clean logs)
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
Order Change Requested
Order Change Approved
Re-pick Items
Re-pack Items
Pick Items
Pack Items
Partial Shipment
Notify Customer
Backorder Created
Ship Backorder
Ship Order
Send Invoice
Payment Reminder Sent
Late Payment
Apply Late Fee
Receive Payment
Complaint Received
Return Processed
Refund Issued
VIP Approval
Gift Packaging

# Multi-step deviations (inserted as a sequence)
Deviations:
Order Change: 0.10 | after=Approve Order | steps=Order Change Requested,Order Change Approved,Re-pick Items,Re-pack Items
Partial Shipment: 0.05 | after=Pack Items | steps=Partial Shipment,Notify Customer,Backorder Created,Ship Backorder
Late Payment: 0.15 | after=Send Invoice | steps=Payment Reminder Sent,Late Payment,Apply Late Fee

CaseAttributes:
CustomerType: New, Returning, VIP
Region: North, South, East, West

EventAttributes:
Resource: Alice, Bob, Carol, Dave
Channel: Email, Phone, Web

# More substantial and interesting variants
Variants:
Standard: Receive Order, Check Credit, Approve Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.6
VIP: Receive Order, Check Credit, Approve Order, VIP Approval, Gift Packaging, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.1
Express: Receive Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment | 0.1
With Return: Receive Order, Check Credit, Approve Order, Pick Items, Pack Items, Ship Order, Send Invoice, Receive Payment, Complaint Received, Return Processed, Refund Issued | 0.2

DefaultDuration: 1440  # 1 day per activity
ActivityDurations:
Receive Order: 60
Check Credit: 240
Approve Order: 120
Order Change Requested: 60
Order Change Approved: 60
Re-pick Items: 120
Re-pack Items: 90
Pick Items: 180
Pack Items: 120
Partial Shipment: 60
Notify Customer: 30
Backorder Created: 30
Ship Backorder: 360
Ship Order: 360
Send Invoice: 60
Payment Reminder Sent: 30
Late Payment: 1440
Apply Late Fee: 15
Receive Payment: 4320  # 3 days
Complaint Received: 30
Return Processed: 240
Refund Issued: 60
VIP Approval: 60
Gift Packaging: 30
```


### 3. Run the generator

```
python generate_synthetic_event_log.py --variables-file variables.txt --output-file synthetic_event_log.csv --n-cases 1000 --random-seed 42 --shuffle-fraction 0 --max-activities 20
```

#### Key CLI options
- `--shuffle-fraction`: Fraction of cases to shuffle activities for realism (default: 0.2). Set to 0 for strict variant order.
- `--deviation-at-end`: If set, deviations are always inserted at the end of the activity sequence (not typical for realism).
- `--random-seed`: Set for reproducible results.
- `--max-activities`: Maximum number of activities per case (default: 8).

**Tip:**
- For strict conformance to variants and realistic deviations, use `--shuffle-fraction 0` (omit `--deviation-at-end`).
- For more realistic, noisy logs, increase `--shuffle-fraction` and omit `--deviation-at-end`.

### 4. Output

The generated CSV will contain one row per event, with columns for case name, activity, timestamp, and all configured attributes.


## Advanced Configuration
- **Multi-step deviations**: Use the `steps=` modifier to insert a sequence of activities for a deviation.
- **Strict placement**: Deviations are only inserted if the placement rule matches the variant path; otherwise, a warning is logged and the deviation is skipped.
- **Timestamps and durations**: Each activity (including deviation steps) gets its own duration and timestamp, reflecting the true process flow and impact of deviations.
- **Variants**: Frequencies should sum to 1.0. Cases are distributed accordingly.
- **Attributes**: Add as many case/event attributes as needed; values are randomly assigned.


## Example Output
| case:concept:name | Activity                | Timestamp           | CustomerType | Region | Resource | Channel |
|-------------------|-------------------------|---------------------|--------------|--------|----------|---------|
| Case_1            | Receive Order           | 2025-07-27 10:00:00 | VIP          | North  | Alice    | Email   |
| Case_1            | Check Credit            | 2025-07-27 10:10:00 | VIP          | North  | Bob      | Phone   |
| Case_1            | Approve Order           | 2025-07-27 10:20:00 | VIP          | North  | Carol    | Web     |
| Case_1            | Order Change Requested  | 2025-07-27 10:25:00 | VIP          | North  | Dave     | Email   |
| Case_1            | Order Change Approved   | 2025-07-27 10:26:00 | VIP          | North  | Alice    | Phone   |
| Case_1            | Re-pick Items           | 2025-07-27 10:28:00 | VIP          | North  | Bob      | Web     |
| Case_1            | Re-pack Items           | 2025-07-27 10:30:00 | VIP          | North  | Carol    | Email   |
| Case_1            | Pick Items              | 2025-07-27 10:33:00 | VIP          | North  | Dave     | Phone   |
| ...               | ...                     | ...                 | ...          | ...    | ...      | ...     |

## License
MIT License

## Author
Your Name
