import os
import random
from datetime import datetime, timedelta
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

# Path to the variables file
import argparse

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
args = parser.parse_args()
variables_file = args.variables_file
output_file = args.output_file
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
                    deviations.append(line)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except IOError as e:
        print(f"IO error occurred while reading '{file_path}': {e}")
    return context, activities, deviations
            elif line.lower().startswith("deviations:"):
                section = "deviations"
                continue
            if section == "context":
                context.append(line)
            elif section == "activities":
                activities.append(line)
            elif section == "deviations":
                deviations.append(line)
    return context, activities, deviations

# Generate synthetic event log
def generate_event_log(context, activities, deviations, n_cases=100, max_activities=8):
    data = []
    for case_id in range(1, n_cases + 1):
        uid = f"Case_{case_id}"
        n_acts = random.randint(3, max_activities)
        path = activities.copy()
        # Randomly insert deviations
        if deviations and random.random() < 0.3:
            dev = random.choice(deviations)
            insert_at = random.randint(1, len(path)-1)
            path.insert(insert_at, dev)
        # Shuffle or reorder for some cases
        if random.random() < 0.2:
            random.shuffle(path)
        # Generate timestamps
        start_time = datetime.now() - timedelta(days=random.randint(0, 365))
        for i, act in enumerate(path[:n_acts]):
            timestamp = start_time + timedelta(minutes=10*i + random.randint(0, 5))
            data.append({
                "UID": uid,
                "Activity": act,
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Read variables
    context, activities, deviations = read_variables(variables_file)
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Synthetic event log saved to {output_file}")
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    event_log = log_converter.apply(df)
    # Save to CSV
    df.to_csv("synthetic_event_log.csv", index=False)
    print("Synthetic event log saved to synthetic_event_log.csv")
