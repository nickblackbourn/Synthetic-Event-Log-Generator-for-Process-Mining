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
                    # Remove comments after value (e.g., '4320  # 3 days')
                    val_clean = val.strip().split()[0] if val.strip() else val.strip()
                    try:
                        activity_durations[name.strip()] = int(val_clean)
                    except ValueError:
                        print(f"Warning: Skipping invalid activity duration value '{val}' for activity '{name.strip()}'")
            elif section == "sequencedurations":
                if ":" in line:
                    seq, val = line.split(":", 1)
                    val_clean = val.strip().split()[0] if val.strip() else val.strip()
                    try:
                        sequence_durations[tuple(s.strip() for s in seq.split(","))] = int(val_clean)
                    except ValueError:
                        print(f"Warning: Skipping invalid sequence duration value '{val}' for sequence '{seq}'")
            elif section == "deviationdurations":
                if ":" in line:
                    name, val = line.split(":", 1)
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
                # Only parse valid deviation lines: must have ':' and 'after='
                if not line or line.startswith('#'):
                    continue
                if ':' in line and 'after=' in line:
                    parts = [p.strip() for p in line.split("|")]
                    name_prob = parts[0]
                    name, prob = name_prob.split(":", 1)
                    dev = {"prob": float(prob.strip()), "placement": None, "placement_type": None, "placement_seq": None, "steps": None}
                    for p in parts[1:]:
                        if p.startswith("before="):
                            dev["placement_type"] = "before"
                            dev["placement_seq"] = [x.strip() for x in p[len("before="):].split(",")]
                        elif p.startswith("after="):
                            dev["placement_type"] = "after"
                            dev["placement_seq"] = [x.strip() for x in p[len("after="):].split(",")]
                        elif p.startswith("steps="):
                            dev["steps"] = [x.strip() for x in p[len("steps="):].split(",")]
                    # Defensive: ensure 'after' is always present
                    if dev["placement_type"] != "after" or not dev["placement_seq"]:
                        raise ValueError(f"Deviation '{name.strip()}' is missing required 'after' anchor. Line: {line}")
                    # For compatibility with rest of code
                    dev['after'] = dev['placement_seq'][0] if dev['placement_type'] == 'after' else None
                    deviations[name.strip()] = dev
                elif line:
                    raise ValueError(f"Malformed deviation line (must have ':' and 'after='): {line}")
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
    # UX-driven: Guarantee all variants and deviations are present as specified
    if not variants:
        variants = [{"name": "Default", "activities": activities, "freq": 1.0}]
    n_cases_list = list(range(1, n_cases + 1))
    variant_case_counts = [int(round(v["freq"] * n_cases)) for v in variants]
    while sum(variant_case_counts) < n_cases:
        variant_case_counts[0] += 1
    while sum(variant_case_counts) > n_cases:
        variant_case_counts[0] -= 1
    case_variant_assignment = []
    for idx, v in enumerate(variants):
        case_variant_assignment += [idx] * variant_case_counts[idx]
    random.shuffle(case_variant_assignment)

    # Prepare deviation assignment: for each deviation, assign to correct number of cases
    deviation_names = list(deviations.keys())
    deviation_probs = {k: v["prob"] for k, v in deviations.items()}
    deviation_steps_set = set()
    for deviation in deviations.values():
        deviation_steps_set.update(deviation['steps'])
    deviation_case_ids = {dev: set(random.sample(n_cases_list, int(round(deviation_probs[dev] * n_cases)))) for dev in deviation_names}

    # Track which deviations were actually placed
    placed_deviation_counts = {dev: 0 for dev in deviation_names}
    missing_deviation_cases = {dev: [] for dev in deviation_names}

    for i, case_id in enumerate(n_cases_list):
        case_name = f"Case_{case_id}"
        variant = variants[case_variant_assignment[i]]
        path = variant["activities"].copy()
        # Insert deviations for this case if preselected
        for dev in deviation_names:
            if case_id in deviation_case_ids[dev]:
                dev_info = deviations[dev]
                anchor = dev_info["after"]
                steps = dev_info["steps"]
                # Find anchor position
                if anchor in path:
                    idx = path.index(anchor)
                    # Insert steps after anchor
                    path = path[:idx+1] + steps + path[idx+1:]
                    placed_deviation_counts[dev] += 1
                else:
                    missing_deviation_cases[dev].append(case_id)
        # Enforce that the first activity is not a deviation step
        if path and path[0] in deviation_steps_set:
            print(f"Warning: Case {case_id} starts with deviation step '{path[0]}'. Skipping this case.")
            continue
        # Build the case events
        case_attr_values = {attr: random.choice(values) for attr, values in case_attributes.items()}
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        prev_acts = []
        prev_duration = None
        timestamp = start_time
        for j, act in enumerate(path):
            duration = get_duration(act, prev_acts, case_attr_values, timing_config)
            timestamp = timestamp + timedelta(minutes=duration)
            event = {
                "case:concept:name": case_name,
                "Activity": act,
                "Timestamp": timestamp.strftime("%d.%m.%Y %H:%M:%S")
            }
            event.update(case_attr_values)
            for attr, values in event_attributes.items():
                event[attr] = random.choice(values)
            data.append(event)
            prev_acts.append(act)
            prev_duration = duration

    # Post-generation validation and user feedback
    for dev in deviation_names:
        expected = int(round(deviation_probs[dev] * n_cases))
        actual = placed_deviation_counts[dev]
        if actual < expected:
            print(f"Warning: Deviation '{dev}' was only placed in {actual} of {expected} requested cases. Missing in cases: {missing_deviation_cases[dev]}")

    # Validate that all activities and deviations are present
    all_activities = set()
    for v in variants:
        all_activities.update(v["activities"])
    for dev in deviations.values():
        all_activities.update(dev["steps"])
    output_activities = set([row["Activity"] for row in data])
    missing_acts = all_activities - output_activities
    extra_acts = output_activities - all_activities
    if missing_acts:
        print(f"Warning: Missing activities in output: {sorted(missing_acts)}")
    if extra_acts:
        print(f"Warning: Extra activities in output: {sorted(extra_acts)}")

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
    # Do NOT convert timestamps to ISO format; preserve custom formatting
    event_log = log_converter.apply(df)
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")