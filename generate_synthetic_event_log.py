import os
import random
from datetime import datetime, timedelta
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
import argparse

def read_variables(file_path):
    # New: Parse timing configuration
    default_duration = 10  # minutes
    activity_durations = {}
    sequence_durations = {}
    deviation_durations = {}
    timing_patterns = []
    # Look for timing config lines
    section = None
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("defaultduration:"):
                # Only use the first integer, ignore comments
                val = line.split(":", 1)[1].strip().split()[0]
                default_duration = int(val)
            elif line.lower().startswith("activitydurations:"):
                section = "activitydurations"
                continue
            elif line.lower().startswith("sequencedurations:"):
                section = "sequencedurations"
                continue
            elif line.lower().startswith("deviationdurations:"):
                section = "deviationdurations"
                continue
            elif line.lower().startswith("timingpatterns:"):
                section = "timingpatterns"
                continue
            if section == "activitydurations":
                if ":" in line:
                    name, val = line.split(":", 1)
                    activity_durations[name.strip()] = int(val.strip())
            elif section == "sequencedurations":
                if ":" in line:
                    seq, val = line.split(":", 1)
                    # Only use the first integer, ignore comments
                    val_clean = val.strip().split()[0] if val.strip() else val.strip()
                    sequence_durations[tuple(s.strip() for s in seq.split(","))] = int(val_clean)
            elif section == "deviationdurations":
                if ":" in line:
                    name, val = line.split(":", 1)
                    # Remove comments after value (e.g., '+1440  # minutes (1 day)')
                    val_clean = val.strip().split()[0] if val.strip() else val.strip()
                    deviation_durations[name.strip()] = val_clean
            elif section == "timingpatterns":
                # Only process lines with a colon, no pipe, and integer value
                if ":" in line and "|" not in line:
                    cond, val = line.split(":", 1)
                    val_clean = val.strip()
                    try:
                        timing_patterns.append((cond.strip(), int(val_clean)))
                    except ValueError:
                        print(f"Warning: Skipping invalid timing pattern value '{val_clean}' on line: {line}")
    context = []
    activities = []
    deviations = {}
    case_attributes = {}
    event_attributes = {}
    variants = []
    section = None
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("context:"):
                section = "context"
                continue
            elif line.lower().startswith("activities:"):
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
            if section == "context":
                context.append(line)
            elif section == "activities":
                activities.append(line)
            elif section == "deviations":
                # Support: DeviationName: prob | before=... or | after=...
                if ":" in line:
                    name_prob, *placement_parts = line.split("|", 1)
                    name, prob = name_prob.split(":", 1)
                    dev = {"prob": float(prob.strip()), "placement": None, "placement_type": None, "placement_seq": None}
                    if placement_parts:
                        placement = placement_parts[0].strip()
                        if placement.startswith("before="):
                            dev["placement_type"] = "before"
                            dev["placement_seq"] = [x.strip() for x in placement[len("before="):].split(",")]
                        elif placement.startswith("after="):
                            dev["placement_type"] = "after"
                            dev["placement_seq"] = [x.strip() for x in placement[len("after="):].split(",")]
                    deviations[name.strip()] = dev
                else:
                    deviations[line] = {"prob": 0.1, "placement": None, "placement_type": None, "placement_seq": None}
            elif section == "caseattributes":
                if ":" in line:
                    name, values = line.split(":", 1)
                    case_attributes[name.strip()] = [v.strip() for v in values.split(",")]
            elif section == "eventattributes":
                if ":" in line:
                    name, values = line.split(":", 1)
                    event_attributes[name.strip()] = [v.strip() for v in values.split(",")]
            elif section == "variants":
                # Format: VariantName: Activity1, Activity2, ... | freq
                if "|" in line:
                    variant_part, freq_part = line.split("|", 1)
                    name, acts = variant_part.split(":", 1)
                    freq = float(freq_part.strip())
                    act_list = [a.strip() for a in acts.split(",")]
                    variants.append({"name": name.strip(), "activities": act_list, "freq": freq})
    return context, activities, deviations, case_attributes, event_attributes, variants, {
        "default": default_duration,
        "activities": activity_durations,
        "sequences": sequence_durations,
        "deviations": deviation_durations,
        "patterns": timing_patterns
    }

def generate_event_log(context, activities, deviations, case_attributes, event_attributes, variants, n_cases=100, max_activities=8, shuffle_fraction=0.2, deviation_at_end=False, timing_config=None):
    """
    Generate a synthetic event log with strict case count, mostly strict variant order, and controlled realism.
    shuffle_fraction: fraction of cases to shuffle (for realism, 0 disables)
    deviation_at_end: if True, always insert deviations at end; else random position
    """
    data = []
    # Helper: get duration for activity/sequence/case
    if timing_config is None:
        timing_config = {
            "default": 10,
            "activities": {},
            "sequences": {},
            "deviations": {},
            "patterns": []
        }
    def get_duration(act, prev_acts, case_attrs, timing_config):
        # Check sequence durations
        for seq, dur in timing_config["sequences"].items():
            if len(seq) <= len(prev_acts) and tuple(prev_acts[-len(seq):]) == seq:
                return dur
        # Check activity durations
        if act in timing_config["activities"]:
            return timing_config["activities"][act]
        # Check timing patterns
        for cond, dur in timing_config["patterns"]:
            # Simple: If CustomerType=VIP and Activity=Pack Items
            if "Activity=" in cond and f"Activity={act}" in cond:
                for attr in case_attrs:
                    if f"{attr}={case_attrs[attr]}" in cond:
                        return dur
        return timing_config["default"]

    # Helper: apply deviation time impact
    def apply_deviation_time(act, deviation, timing_config):
        impact = timing_config["deviations"].get(deviation)
        if impact:
            # Remove comments after value (e.g., '+1440  # minutes (1 day)')
            impact_clean = impact.split()[0] if impact else impact
            if impact_clean.startswith("+"):
                try:
                    return int(impact_clean[1:])
                except ValueError:
                    print(f"Warning: Invalid deviation impact value '{impact_clean}' for deviation '{deviation}'")
                    return 0
            elif impact_clean.startswith("x"):
                # Only support xN for previous duration
                return impact_clean
        return 0
    deviation_names = list(deviations.keys())
    deviation_probs = {k: v["prob"] for k, v in deviations.items()}
    if not variants:
        variants = [{"name": "Default", "activities": activities, "freq": 1.0}]
    n_cases_list = list(range(1, n_cases + 1))
    # Assign cases to variants based on frequencies, always sum to n_cases
    variant_case_counts = [int(round(v["freq"] * n_cases)) for v in variants]
    while sum(variant_case_counts) < n_cases:
        variant_case_counts[0] += 1
    while sum(variant_case_counts) > n_cases:
        variant_case_counts[0] -= 1
    case_variant_assignment = []
    for idx, v in enumerate(variants):
        case_variant_assignment += [idx] * variant_case_counts[idx]
    random.shuffle(case_variant_assignment)
    # Preselect cases for each deviation to match requested percentages
    deviation_cases = {dev: set(random.sample(n_cases_list, int(round(deviation_probs[dev] * n_cases)))) for dev in deviation_names}
    for i, case_id in enumerate(n_cases_list):
        case_name = f"Case_{case_id}"
        variant = variants[case_variant_assignment[i]]
        path = variant["activities"].copy()
        # Insert deviations for this case if preselected
        for dev in deviation_names:
            if case_id in deviation_cases[dev]:
                dev_info = deviations[dev]
                placement_type = dev_info["placement_type"]
                placement_seq = dev_info["placement_seq"]
                # Strict business rules for deviation placement
                if dev == "Late Payment":
                    # Only after 'Send Invoice'
                    if "Send Invoice" in path:
                        idx = path.index("Send Invoice")
                        path.insert(idx + 1, dev)
                    else:
                        print(f"Warning: Could not place 'Late Payment' after 'Send Invoice' in case {case_name}")
                elif dev == "Partial Shipment":
                    # After 'Pick Items' or 'Pack Items', prefer last occurrence
                    idx = -1
                    for act in ["Pack Items", "Pick Items"]:
                        if act in path:
                            idx = max(idx, max([i for i, a in enumerate(path) if a == act]))
                    if idx != -1:
                        path.insert(idx + 1, dev)
                    else:
                        print(f"Warning: Could not place 'Partial Shipment' after 'Pick Items' or 'Pack Items' in case {case_name}")
                elif dev == "Order Change":
                    # After 'Approve Order' and before 'Ship Order'
                    if "Approve Order" in path and "Ship Order" in path:
                        idx_approve = path.index("Approve Order")
                        idx_ship = path.index("Ship Order")
                        # Place after 'Approve Order' but before 'Ship Order'
                        insert_at = idx_approve + 1 if idx_approve + 1 < idx_ship else idx_ship
                        path.insert(insert_at, dev)
                    else:
                        print(f"Warning: Could not place 'Order Change' after 'Approve Order' and before 'Ship Order' in case {case_name}")
                elif deviation_at_end:
                    path.append(dev)
                elif placement_type and placement_seq:
                    seq_len = len(placement_seq)
                    found = False
                    for idx in range(len(path) - seq_len + 1):
                        if path[idx:idx+seq_len] == placement_seq:
                            if placement_type == "before":
                                path.insert(idx, dev)
                            elif placement_type == "after":
                                path.insert(idx+seq_len, dev)
                            found = True
                            break
                    if not found:
                        if placement_type == "before":
                            path.insert(0, dev)
                        else:
                            path.append(dev)
                else:
                    insert_at = random.randint(1, len(path)) if len(path) > 1 else 1
                    path.insert(insert_at, dev)
        # Shuffle for a fraction of cases (for realism)
        if random.random() < shuffle_fraction:
            random.shuffle(path)
        n_acts = min(len(path), max_activities)
        truncated_path = path[:n_acts]
        required_devs = [dev for dev in deviation_names if case_id in deviation_cases[dev]]
        for dev in required_devs:
            if dev not in truncated_path:
                truncated_path = [dev] + truncated_path[:-1]
        case_attr_values = {attr: random.choice(values) for attr, values in case_attributes.items()}
        # Generate timestamps and event attributes
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        prev_acts = []
        prev_duration = None
        timestamp = start_time
        for j, act in enumerate(truncated_path):
            # Duration logic
            duration = get_duration(act, prev_acts, case_attr_values, timing_config)
            # If deviation, apply impact
            if act in deviation_names:
                impact = apply_deviation_time(act, act, timing_config)
                if isinstance(impact, int):
                    duration += impact
                elif isinstance(impact, str) and impact.startswith('x') and prev_duration:
                    duration = int(float(impact[1:]) * prev_duration)
            timestamp = timestamp + timedelta(minutes=duration)
            event = {
                "case:concept:name": case_name,
                "Activity": act,
                "Timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            }
            event.update(case_attr_values)
            for attr, values in event_attributes.items():
                event[attr] = random.choice(values)
            data.append(event)
            prev_acts.append(act)
            prev_duration = duration
    return pd.DataFrame(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a synthetic event log.")
    parser.add_argument(
        "--variables-file",
        type=str,
        default=os.environ.get("VARIABLES_FILE", "variables.txt"),
        help="Path to the variables file (default: variables.txt or $VARIABLES_FILE env var)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="synthetic_event_log.csv",
        help="Path to the output CSV file (default: synthetic_event_log.csv)",
    )
    parser.add_argument(
        "--n-cases",
        type=int,
        default=100,
        help="Number of cases to generate (default: 100)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)",
    )
    parser.add_argument(
        "--shuffle-fraction",
        type=float,
        default=0.2,
        help="Fraction of cases to shuffle for realism (default: 0.2)",
    )
    parser.add_argument(
        "--deviation-at-end",
        action="store_true",
        help="If set, always insert deviations at the end of the activity sequence.",
    )
    parser.add_argument(
        "--max-activities",
        type=int,
        default=8,
        help="Maximum number of activities per case (default: 8)",
    )
    args = parser.parse_args()
    if args.random_seed is not None:
        random.seed(args.random_seed)
    variables_file = args.variables_file
    output_file = args.output_file
    n_cases = args.n_cases
    shuffle_fraction = args.shuffle_fraction
    deviation_at_end = args.deviation_at_end
    max_activities = args.max_activities
    context, activities, deviations, case_attributes, event_attributes, variants, timing_config = read_variables(variables_file)
    df = generate_event_log(
        context, activities, deviations, case_attributes, event_attributes, variants,
        n_cases=n_cases, max_activities=max_activities,
        shuffle_fraction=shuffle_fraction, deviation_at_end=deviation_at_end,
        timing_config=timing_config
    )
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")