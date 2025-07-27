import os
import random
from datetime import datetime, timedelta
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
import argparse

def read_variables(file_path):
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
                if ":" in line:
                    name, prob = line.split(":", 1)
                    deviations[name.strip()] = float(prob.strip())
                else:
                    deviations[line] = 0.1
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
    return context, activities, deviations, case_attributes, event_attributes, variants

def generate_event_log(context, activities, deviations, case_attributes, event_attributes, variants, n_cases=100, max_activities=8, shuffle_fraction=0.2, deviation_at_end=False):
    """
    Generate a synthetic event log with strict case count, mostly strict variant order, and controlled realism.
    shuffle_fraction: fraction of cases to shuffle (for realism, 0 disables)
    deviation_at_end: if True, always insert deviations at end; else random position
    """
    data = []
    deviation_names = list(deviations.keys())
    deviation_probs = deviations
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
                if deviation_at_end:
                    path.append(dev)
                else:
                    insert_at = random.randint(1, len(path)) if len(path) > 1 else 1
                    path.insert(insert_at, dev)
        # Shuffle for a fraction of cases (for realism)
        if random.random() < shuffle_fraction:
            random.shuffle(path)
        # Truncate if needed, but warn if truncation would cut variant activities
        n_acts = min(len(path), max_activities)
        truncated_path = path[:n_acts]
        # Ensure all deviations for this case are present in truncated path
        required_devs = [dev for dev in deviation_names if case_id in deviation_cases[dev]]
        for dev in required_devs:
            if dev not in truncated_path:
                truncated_path = [dev] + truncated_path[:-1]
        # Assign case attributes
        case_attr_values = {attr: random.choice(values) for attr, values in case_attributes.items()}
        # Generate timestamps and event attributes
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        for j, act in enumerate(truncated_path):
            timestamp = start_time + timedelta(minutes=10*j + random.randint(0, 5))
            event = {
                "case:concept:name": case_name,
                "Activity": act,
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            event.update(case_attr_values)
            for attr, values in event_attributes.items():
                event[attr] = random.choice(values)
            data.append(event)
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
    context, activities, deviations, case_attributes, event_attributes, variants = read_variables(variables_file)
    df = generate_event_log(
        context, activities, deviations, case_attributes, event_attributes, variants,
        n_cases=n_cases, max_activities=max_activities,
        shuffle_fraction=shuffle_fraction, deviation_at_end=deviation_at_end
    )
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")