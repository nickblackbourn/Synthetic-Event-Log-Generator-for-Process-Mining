def strict_test(csv_path, variables_path):
    df = pd.read_csv(csv_path)
    with open(variables_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    section = None
    activities = []
    deviations = []
    case_attributes = {}
def parse_variables_txt(path):
    activities = set()
    variants = {}
    deviations = set()
    with open(path, encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
    section = None
    for line in lines:
        if line.lower().startswith('activities:'):
            section = 'activities'
            continue
        elif line.lower().startswith('variants:'):
            section = 'variants'
            continue
        elif line.lower().startswith('deviations:'):
            section = 'deviations'
            continue
        if section == 'activities':
            activities.add(line)
        elif section == 'variants':
            if ':' in line and '|' in line:
                name, rest = line.split(':', 1)
                acts, freq = rest.split('|', 1)
                variants[name.strip()] = [a.strip() for a in acts.split(',')]
        elif section == 'deviations':
            if ':' in line and 'steps=' in line:
                # e.g. Order Change: 0.10 | after=Approve Order | steps=Order Change Requested,Order Change Approved,Re-pick Items,Re-pack Items
                steps = re.search(r'steps=([^|]+)', line)
                if steps:
                    deviations.update([s.strip() for s in steps.group(1).split(',')])
    return activities, variants, deviations
def main():
    activities, variants, deviations = parse_variables_txt('variables.txt')
    expected_activities = activities | deviations
    df = pd.read_csv('synthetic_event_log.csv')
    found_activities = set(df['Activity'].unique())
    missing = expected_activities - found_activities
    extra = found_activities - expected_activities
    if missing:
        print('STRICT TEST FAILED:')
        print(f'- Missing activities in CSV: {sorted(missing)}')
    if extra:
        print('STRICT TEST FAILED:')
        print(f'- Extra activities in CSV: {sorted(extra)}')
    if not missing and not extra:
        print('STRICT TEST PASSED: All activities present as specified.')
    main()
import pandas as pd
import yaml
import difflib

def main():
    # Load YAML config
    with open('variables.txt', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    activities = set(config.get('activities', []))
    deviations = set()
    for dev in config.get('deviations', []):
        deviations.update(dev.get('steps', []))
    expected_activities = activities | deviations
    case_attributes = config.get('case_attributes', {})
    event_attributes = config.get('event_attributes', {})
    variants = config.get('variants', [])

    df = pd.read_csv('synthetic_event_log.csv')
    found_activities = set(df['Activity'].unique())
    missing = expected_activities - found_activities
    extra = found_activities - expected_activities
    errors = []
    if missing:
        errors.append(f"Missing activities in CSV: {sorted(missing)}")
    if extra:
        errors.append(f"Extra activities in CSV: {sorted(extra)}")

    # Case attributes
    for attr, values in case_attributes.items():
        if attr not in df.columns:
            errors.append(f"Case attribute '{attr}' missing from CSV columns")
        else:
            missing_vals = set(values) - set(df[attr].unique())
            extra_vals = set(df[attr].unique()) - set(values)
            if missing_vals:
                errors.append(f"Case attribute '{attr}' missing values: {sorted(missing_vals)}")
            if extra_vals:
                errors.append(f"Case attribute '{attr}' has unexpected values: {sorted(extra_vals)}")
    # Event attributes
    for attr, values in event_attributes.items():
        if attr not in df.columns:
            errors.append(f"Event attribute '{attr}' missing from CSV columns")
        else:
            missing_vals = set(values) - set(df[attr].unique())
            extra_vals = set(df[attr].unique()) - set(values)
            if missing_vals:
                errors.append(f"Event attribute '{attr}' missing values: {sorted(missing_vals)}")
            if extra_vals:
                errors.append(f"Event attribute '{attr}' has unexpected values: {sorted(extra_vals)}")
    # Variants: check if all variant activity sequences appear in at least one case
    for v in variants:
        found = False
        seq = v.get('sequence', v.get('activities', []))
        for case in df["case:concept:name"].unique():
            acts = df[df["case:concept:name"] == case]["Activity"].tolist()
            if difflib.SequenceMatcher(None, acts, seq).ratio() > 0.95:
                found = True
                break
        if not found:
            errors.append(f"Variant '{v.get('name','?')}' activity sequence not found in any case (or not exact)")
    # Report
    if errors:
        print("STRICT TEST FAILED:")
        for err in errors:
            print("-", err)
    else:
        print("STRICT TEST PASSED: All variables exactly reflected in CSV.")

if __name__ == "__main__":
    main()
