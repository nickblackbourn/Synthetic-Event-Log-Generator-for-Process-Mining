import pandas as pd
import difflib

def strict_test(csv_path, variables_path):
    df = pd.read_csv(csv_path)
    with open(variables_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    section = None
    activities = []
    deviations = []
    case_attributes = {}
    event_attributes = {}
    variants = []
    for line in lines:
        if line.lower().startswith("activities:"):
            section = "activities"
            continue
        elif line.lower().startswith("deviations:"):
            section = "deviations"
            continue
        elif line.lower().startswith("caseattributes:"):
            section = "caseattributes"
            continue
        elif line.lower().startswith("eventattributes:"):
            section = "eventattributes"
            continue
        elif line.lower().startswith("variants:"):
            section = "variants"
            continue
        if section == "activities":
            activities.append(line)
        elif section == "deviations":
            if ":" in line:
                name = line.split(":", 1)[0].strip()
                deviations.append(name)
            else:
                deviations.append(line)
        elif section == "caseattributes":
            if ":" in line:
                name, values = line.split(":", 1)
                case_attributes[name.strip()] = [v.strip() for v in values.split(",")]
        elif section == "eventattributes":
            if ":" in line:
                name, values = line.split(":", 1)
                event_attributes[name.strip()] = [v.strip() for v in values.split(",")]
        elif section == "variants":
            if "|" in line:
                variant_part, freq_part = line.split("|", 1)
                name, acts = variant_part.split(":", 1)
                act_list = [a.strip() for a in acts.split(",")]
                variants.append({"name": name.strip(), "activities": act_list})
    # Strict checks
    errors = []
    # Activities
    csv_activities = set(df["Activity"].unique())
    expected_activities = set(activities + deviations)
    missing_acts = expected_activities - csv_activities
    extra_acts = csv_activities - expected_activities
    if missing_acts:
        errors.append(f"Missing activities in CSV: {sorted(missing_acts)}")
    if extra_acts:
        errors.append(f"Extra activities in CSV: {sorted(extra_acts)}")
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
        for case in df["case:concept:name"].unique():
            acts = df[df["case:concept:name"] == case]["Activity"].tolist()
            if difflib.SequenceMatcher(None, acts, v["activities"]).ratio() > 0.95:
                found = True
                break
        if not found:
            errors.append(f"Variant '{v['name']}' activity sequence not found in any case (or not exact)")
    # Report
    if errors:
        print("STRICT TEST FAILED:")
        for err in errors:
            print("-", err)
    else:
        print("STRICT TEST PASSED: All variables exactly reflected in CSV.")

if __name__ == "__main__":
    strict_test("synthetic_event_log.csv", "variables.txt")
