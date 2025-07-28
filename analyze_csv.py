import pandas as pd

def analyze_csv(csv_path, variables_path):
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} events from {csv_path}")
    # Read variables.txt
    with open(variables_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    # Extract activities, deviations, case attributes, event attributes, variants
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
    # Analysis
    print("\n--- Activities ---")
    print("Configured:", activities)
    print("Found in CSV:", sorted(df["Activity"].unique()))
    print("\n--- Deviations ---")
    print("Configured:", deviations)
    print("Found in CSV:", sorted(set(df["Activity"]) & set(deviations)))
    print("\n--- Case Attributes ---")
    for attr, values in case_attributes.items():
        print(f"{attr}: Configured {values}, Found {sorted(df[attr].unique()) if attr in df.columns else 'Not in CSV'}")
    print("\n--- Event Attributes ---")
    for attr, values in event_attributes.items():
        print(f"{attr}: Configured {values}, Found {sorted(df[attr].unique()) if attr in df.columns else 'Not in CSV'}")
    print("\n--- Variants ---")
    print("Configured:", [v["name"] for v in variants])
    print("Sample case activity sequences:")
    for case in df["case:concept:name"].unique()[:5]:
        acts = df[df["case:concept:name"] == case]["Activity"].tolist()
        print(f"{case}: {acts}")

if __name__ == "__main__":
    analyze_csv("synthetic_event_log.csv", "variables.txt")
