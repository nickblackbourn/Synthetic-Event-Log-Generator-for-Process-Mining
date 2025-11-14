# Training Guide: Synthetic Event Log Generator (ELI5 Version)

## What This Tool Does (In Simple Terms)

Imagine you run a pizza restaurant and want to understand how orders flow through your business. This tool creates fake (but realistic) order data that shows:
- How customers place orders
- What can go wrong (like late deliveries or order changes)
- Different types of customers (VIP, regular, etc.)

Instead of waiting months to collect real data, you can generate thousands of realistic examples in seconds!

## Before We Start - What You Need

### Step 1: Check if Python is Installed
1. Press `Windows Key + R`
2. Type `cmd` and press Enter
3. Type `python --version` and press Enter
4. If you see a version number (like `Python 3.9.0`), you're good to go!
5. If you get an error, you need to install Python first

### Step 2: Open the Project Folder
1. Download the project files to your computer
2. Right-click on the project folder
3. Select "Open with Code" (if you have VS Code installed)

## Understanding the Configuration File

### What is `variables.txt`?
Think of this file as a recipe book for your fake data. It tells the computer:
- What steps happen in your process (like "Receive Order", "Make Pizza", "Deliver")
- What can go wrong (like "Customer Changes Order", "Delivery is Late")
- What types of customers you have (VIP, Regular, New)

### Key Sections Explained:

#### 1. **Activities** (The Steps in Your Process)
```yaml
activities:
  - Receive Order
  - Check Credit
  - Approve Order
  - Pick Items
  - Pack Items
  - Ship Order
```
*Think of these as the steps an order goes through from start to finish*

#### 2. **Variants** (Different Ways Things Can Happen)
```yaml
variants:
  - name: Standard
    sequence: [Receive Order, Check Credit, Approve Order, Pick Items, Pack Items, Ship Order]
    frequency: 0.6  # This happens 60% of the time
  - name: VIP
    sequence: [Receive Order, VIP Approval, Gift Packaging, Pick Items, Pack Items, Ship Order]
    frequency: 0.1  # This happens 10% of the time
```
*Different types of customers get different treatment*

#### 3. **Deviations** (When Things Go Wrong)
```yaml
deviations:
  - name: Late Payment
    probability: 0.15  # Happens 15% of the time
    after: Send Invoice  # This problem happens after we send the bill
    steps: [Payment Reminder Sent, Late Payment, Apply Late Fee]
```
*These are the problems that can occur and how we handle them*

#### 4. **Attributes** (Customer Information)
```yaml
case_attributes:
  CustomerType: [New, Returning, VIP]
  Region: [North, South, East, West]
```
*Information about each customer that might affect how we treat them*

## Step-by-Step: Generating Your Data

### Step 1: Open the Terminal
1. In VS Code, press `Ctrl + Shift + `` (backtick key)
2. A terminal window will appear at the bottom

### Step 2: Activate the Python Environment
1. Type this command and press Enter:
   ```
   .venv\Scripts\python.exe
   ```
2. You should see the Python version appear

### Step 3: Generate Your Data
1. Type this command to create 1,000 fake orders:
   ```
   .venv\Scripts\python.exe generate_synthetic_event_log.py --n-cases 1000
   ```
2. Press Enter and wait a few seconds
3. You'll see a message: "Synthetic event log saved to synthetic_event_log.csv"

### Step 4: Check Your Results
1. Type this command to verify everything worked:
   ```
   .venv\Scripts\python.exe qa_event_log.py --all
   ```
2. This will show you a summary of what was created

## Understanding Your Results

### The Output File (`synthetic_event_log.csv`)
This file contains your fake data in a format that Excel can open. Each row represents one step in one customer's journey.

| Case Name | Activity | Timestamp | Customer Type | Region |
|-----------|----------|-----------|---------------|---------|
| Case_1 | Receive Order | 2025-07-27 10:00:00 | VIP | North |
| Case_1 | Check Credit | 2025-07-27 10:10:00 | VIP | North |
| Case_2 | Receive Order | 2025-07-27 11:00:00 | New | East |

## Common Questions & Troubleshooting

### Q: "I want more/fewer fake customers"
**A:** Change the number in the command:
- For 500 customers: `--n-cases 500`
- For 10,000 customers: `--n-cases 10000`

### Q: "I want different types of problems to occur"
**A:** Edit the `variables.txt` file:
1. Find the `deviations:` section
2. Change the `probability:` numbers (0.1 = 10%, 0.2 = 20%, etc.)
3. Save the file and generate new data

### Q: "I want to add new steps to my process"
**A:** Edit the `variables.txt` file:
1. Find the `activities:` section
2. Add your new step to the list
3. Update the `variants:` section to include your new step
4. Save and generate new data

### Q: "The tool says some problems couldn't be placed"
**A:** This is normal! It means the tool is being smart about when problems can occur. For example, a "Late Payment" problem can only happen to customers who actually get invoiced.

## Tips for Your Training Session

### For the Trainer:
1. **Start with the pizza restaurant analogy** - it helps people understand the concept
2. **Show the `variables.txt` file first** - let people see how human-readable it is
3. **Generate a small dataset first** (100 cases) so people can see results quickly
4. **Open the CSV in Excel** to show the actual output
5. **Let participants modify simple things** like changing the number of cases

### Common Mistakes to Avoid:
- Don't edit the Python files (`.py`) unless you know what you're doing
- Always save `variables.txt` after making changes
- Make sure the frequencies in variants add up to 1.0 (100%)
- Don't use special characters in activity names

### Hands-On Exercise Ideas:
1. **Change the number of cases** from 100 to 500
2. **Add a new customer type** (like "Premium") to the attributes
3. **Modify a deviation probability** and see how it affects the output
4. **Create a new variant** for rush orders

## Next Steps After Training

Once people are comfortable with the basics:
1. They can create their own process models
2. They can use the generated data in process mining tools
3. They can experiment with different business scenarios
4. They can share their configurations with colleagues

## Getting Help

If something goes wrong:
1. Check that all commands are typed exactly as shown
2. Make sure you're in the right folder
3. Verify that `variables.txt` is saved after any changes
4. Try generating a small number of cases first (like 10) to test

Remember: This tool is designed to be safe to experiment with. You can't break anything by trying different settings!
