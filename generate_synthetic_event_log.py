# pip install pm4py
# pip install pandas
# pip install pyyaml
import os
import random
from datetime import datetime, timedelta
import pandas as pd
import argparse
import yaml
from pm4py.objects.conversion.log import converter as log_converter

def read_variables(file_path):
    """
    Load process configuration from a YAML file.
    Returns: context, activities, activity_durations, case_attributes, event_attributes, variants, deviations
    """
    with open(file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    context = config.get("context", "")
    activities = config.get("activities", [])
    activity_durations = config.get("activity_durations", {})
    case_attributes = config.get("case_attributes", {})
    event_attributes = config.get("event_attributes", {})
    variants = config.get("variants", [])
    deviations = config.get("deviations", [])
    return context, activities, activity_durations, case_attributes, event_attributes, variants, deviations

def generate_event_log(context, activities, deviations, case_attributes, event_attributes, variants, n_cases=100, max_activities=8):
    """
    Generate a synthetic event log with strict case count, mostly strict variant order, and controlled realism.
    shuffle_fraction: fraction of cases to shuffle (for realism, 0 disables)
    deviation_at_end: if True, always insert deviations at end; else random position
    """
    data = []
    # Helper: get duration for activity
    def get_duration(act, activity_durations):
        return activity_durations.get(act, activity_durations.get("Default", 10))

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
        variants = [{"name": "Default", "sequence": activities, "frequency": 1.0}]
    n_cases_list = list(range(1, n_cases + 1))
    variant_case_counts = [int(round(v.get("frequency", v.get("freq", 0)) * n_cases)) for v in variants]
    while sum(variant_case_counts) < n_cases:
        variant_case_counts[0] += 1
    while sum(variant_case_counts) > n_cases:
        variant_case_counts[0] -= 1

    # Helper: check if a case's attributes match a filter dict (all keys/values must match)
    def attributes_match(case_attrs, filter_attrs):
        if not filter_attrs:
            return True
        for k, v in filter_attrs.items():
            if case_attrs.get(k) != v:
                return False
        return True

    # Precompute all possible case attribute combinations
    from itertools import product
    attr_keys = list(case_attributes.keys())
    attr_values_product = list(product(*[case_attributes[k] for k in attr_keys]))
    all_case_attr_combos = [dict(zip(attr_keys, vals)) for vals in attr_values_product]

    # For each case, assign attributes, then select allowed variants
    case_attr_values_list = []
    for _ in n_cases_list:
        case_attr_values_list.append(random.choice(all_case_attr_combos))

    # For each variant, precompute which attribute combos it allows
    variant_allowed_attrs = []
    for v in variants:
        filter_attrs = v.get("attributes", {})
        allowed = [i for i, attrs in enumerate(case_attr_values_list) if attributes_match(attrs, filter_attrs)]
        variant_allowed_attrs.append(set(allowed))

    # Assign variants to cases, respecting attribute filters and frequencies
    case_variant_assignment = [None] * n_cases
    remaining_counts = variant_case_counts.copy()
    for idx, allowed_idxs in enumerate(variant_allowed_attrs):
        count = remaining_counts[idx]
        # Find available cases for this variant
        available = [i for i in allowed_idxs if case_variant_assignment[i] is None]
        chosen = random.sample(available, min(count, len(available)))
        for i in chosen:
            case_variant_assignment[i] = idx
        remaining_counts[idx] -= len(chosen)
    # Any unassigned cases: assign to first variant (fallback)
    for i in range(n_cases):
        if case_variant_assignment[i] is None:
            case_variant_assignment[i] = 0

    # Prepare deviation assignment: for each deviation, assign to correct number of cases, respecting attribute filters
    deviation_names = [dev['name'] for dev in deviations]
    deviation_probs = {dev['name']: dev['probability'] for dev in deviations}
    deviation_steps_set = set()
    for dev in deviations:
        deviation_steps_set.update(dev['steps'])
    # For each deviation, only assign to cases whose attributes match
    deviation_case_ids = {}
    for dev in deviations:
        filter_attrs = dev.get("attributes", {})
        eligible_cases = [i+1 for i, attrs in enumerate(case_attr_values_list) if attributes_match(attrs, filter_attrs)]
        n_assign = int(round(deviation_probs[dev['name']] * n_cases))
        deviation_case_ids[dev['name']] = set(random.sample(eligible_cases, min(n_assign, len(eligible_cases))))

    # Track which deviations were actually placed
    placed_deviation_counts = {dev: 0 for dev in deviation_names}
    missing_deviation_cases = {dev: [] for dev in deviation_names}

    for i, case_id in enumerate(n_cases_list):
        case_name = f"Case_{case_id}"
        case_attr_values = case_attr_values_list[i-1] if case_id > 0 else case_attr_values_list[0]
        variant = variants[case_variant_assignment[i-1] if case_id > 0 else 0]
        path = variant.get("sequence", variant.get("activities", [])).copy()
        # Insert deviations for this case if preselected
        for dev in deviations:
            dev_name = dev['name']
            if case_id in deviation_case_ids[dev_name]:
                anchor = dev['after']
                steps = dev['steps']
                # Find anchor position
                if anchor in path:
                    idx = path.index(anchor)
                    # Insert steps after anchor
                    path = path[:idx+1] + steps + path[idx+1:]
                    placed_deviation_counts[dev_name] += 1
                else:
                    missing_deviation_cases[dev_name].append(case_id)
        # Enforce that the first activity is not a deviation step
        if path and path[0] in deviation_steps_set:
            print(f"Warning: Case {case_id} starts with deviation step '{path[0]}'. Skipping this case.")
            continue
        # Build the case events
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        timestamp = start_time
        for j, act in enumerate(path):
            duration = get_duration(act, activity_durations)
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

    # Post-generation validation and user feedback
    for dev in deviation_names:
        expected = int(round(deviation_probs[dev] * n_cases))
        actual = placed_deviation_counts[dev]
        if actual < expected:
            print(f"Warning: Deviation '{dev}' was only placed in {actual} of {expected} requested cases. Missing in cases: {missing_deviation_cases[dev]}")

    # Validate that all activities and deviations are present
    all_activities = set()
    for v in variants:
        all_activities.update(v.get("sequence", v.get("activities", [])))
    for dev in deviations:
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
    max_activities = args.max_activities
    context, activities, activity_durations, case_attributes, event_attributes, variants, deviations = read_variables(variables_file)
    df = generate_event_log(
        context, activities, deviations, case_attributes, event_attributes, variants,
        n_cases=n_cases, max_activities=max_activities
    )
    # Do NOT convert timestamps to ISO format; preserve custom formatting
    event_log = log_converter.apply(df)
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")