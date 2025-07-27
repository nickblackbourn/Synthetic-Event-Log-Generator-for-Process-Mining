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
            if section == "context":
                context.append(line)
            elif section == "activities":
                activities.append(line)
            elif section == "deviations":
                # Support "DeviationName: probability" or just name (default 0.1)
                if ":" in line:
                    name, prob = line.split(":", 1)
                    deviations[name.strip()] = float(prob.strip())
                else:
                    deviations[line] = 0.1
    return context, activities, deviations

def generate_event_log(context, activities, deviations, n_cases=100, max_activities=8):
    data = []
    deviation_names = list(deviations.keys())
    deviation_probs = deviations
    # Preselect cases for each deviation to match requested percentages
    n_cases_list = list(range(1, n_cases + 1))
    deviation_cases = {dev: set(random.sample(n_cases_list, int(round(deviation_probs[dev] * n_cases)))) for dev in deviation_names}
    for case_id in n_cases_list:
        case_name = f"Case_{case_id}"
        n_acts = random.randint(3, max_activities)
        path = activities.copy()
        # Insert deviations for this case if preselected
        for dev in deviation_names:
            if case_id in deviation_cases[dev]:
                insert_at = random.randint(1, len(path)-1) if len(path) > 1 else 1
                path.insert(insert_at, dev)
        # Shuffle or reorder for some cases
        if random.random() < 0.2:
            random.shuffle(path)
        # Ensure all deviations for this case are present in truncated path
        # (If not, move them to the front)
        required_devs = [dev for dev in deviation_names if case_id in deviation_cases[dev]]
        truncated_path = path[:n_acts]
        for dev in required_devs:
            if dev not in truncated_path:
                # Insert at front if missing
                truncated_path = [dev] + truncated_path[:-1]
        # Generate timestamps
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        for i, act in enumerate(truncated_path):
            timestamp = start_time + timedelta(minutes=10*i + random.randint(0, 5))
            data.append({
                "case:concept:name": case_name,
                "Activity": act,
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
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
    args = parser.parse_args()
    variables_file = args.variables_file
    output_file = args.output_file
    n_cases = args.n_cases
    context, activities, deviations = read_variables(variables_file)
    df = generate_event_log(context, activities, deviations, n_cases=n_cases)
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")