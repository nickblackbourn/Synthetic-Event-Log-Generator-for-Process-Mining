import pandas as pd
from collections import Counter

def test_deviation_and_variant_ratios(event_log_path, variables_path, n_cases=100):
    # Read event log
    df = pd.read_csv(event_log_path)
    # Read variables.txt for deviation probabilities and variant frequencies
    deviations = {}
    variants = []
    with open(variables_path, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('deviations:'):
                section = 'deviations'
                continue
            elif line.lower().startswith('variants:'):
                section = 'variants'
                continue
            if section == 'deviations':
                if ':' in line:
                    name_prob, *_ = line.split('|', 1)
                    try:
                        name, prob = name_prob.split(':', 1)
                        prob_val = float(prob.strip())
                        deviations[name.strip()] = prob_val
                    except Exception as e:
                        print(f"Warning: Skipping malformed deviation line: '{line}' ({e})")
            elif section == 'variants':
                if '|' in line:
                    try:
                        variant_part, freq_part = line.split('|', 1)
                        name, acts = variant_part.split(':', 1)
                        freq = float(freq_part.strip())
                        variants.append((name.strip(), freq))
                    except Exception as e:
                        print(f"Warning: Skipping malformed variant line: '{line}' ({e})")
    # Test deviation ratios
    case_deviations = {dev: set() for dev in deviations}
    for _, row in df.iterrows():
        case = row['case:concept:name']
        act = row['Activity']
        if act in deviations:
            case_deviations[act].add(case)
    print('\nDeviation ratios:')
    for dev, prob in deviations.items():
        actual = len(case_deviations[dev])
        expected = int(round(prob * n_cases))
        print(f"Deviation '{dev}': actual={actual}, expected={expected}, ratio={actual/n_cases:.2f}")
    # Test variant ratios
    case_variants = Counter()
    # Variant detection: match first activity sequence to variant definition
    variant_defs = {}
    for name, freq in variants:
        variant_defs[name] = None  # Will fill below
    # Build variant activity lists from variables.txt
    with open(variables_path, 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.lower().startswith('variants:'):
                section = 'variants'
                continue
            if section == 'variants' and '|' in line:
                variant_part, _ = line.split('|', 1)
                name, acts = variant_part.split(':', 1)
                act_list = tuple(a.strip() for a in acts.split(','))
                variant_defs[name.strip()] = act_list
    # For each case, get its activity sequence
    case_activities = {}
    for _, row in df.iterrows():
        case = row['case:concept:name']
        act = row['Activity']
        case_activities.setdefault(case, []).append(act)
    for case, acts in case_activities.items():
        for name, act_list in variant_defs.items():
            if tuple(acts[:len(act_list)]) == act_list:
                case_variants[name] += 1
                break
    print('\nVariant ratios:')
    for name, freq in variants:
        actual = case_variants[name]
        expected = int(round(freq * n_cases))
        print(f"Variant '{name}': actual={actual}, expected={expected}, ratio={actual/n_cases:.2f}")
    print("\nSummary:")
    print(f"Total cases: {n_cases}")
    print(f"Total deviations: {sum(len(v) for v in case_deviations.values())}")
    print(f"Total variants: {len(variants)}")

if __name__ == "__main__":
    test_deviation_and_variant_ratios('synthetic_event_log.csv', 'variables.txt', n_cases=100)
