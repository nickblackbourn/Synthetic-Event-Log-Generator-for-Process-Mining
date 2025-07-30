import argparse
import pandas as pd
import yaml
from collections import Counter

def strict_test(df, variables):
    print("\n=== STRICT TEST ===")
    all_activities = set(variables.get('activities', []))
    all_deviation_steps = set()
    for dev in variables.get('deviations', []):
        all_deviation_steps.update(dev.get('steps', []))
    expected_activities = all_activities | all_deviation_steps
    found_activities = set(df['Activity'].unique())
    missing = expected_activities - found_activities
    extra = found_activities - expected_activities
    if missing:
        print(f'- Missing activities in CSV: {sorted(missing)}')
    if extra:
        print(f'- Extra activities in CSV: {sorted(extra)}')
    if not missing and not extra:
        print('STRICT TEST PASSED: All activities present as specified.')

def analyze_summary(df, variables):
    print("\n=== SUMMARY ===")
    print(f"Total events: {len(df)}")
    print(f"Unique cases: {df['case:concept:name'].nunique()}")
    print(f"Activities: {sorted(df['Activity'].unique())}")
    for attr in variables.get('case_attributes', {}):
        print(f"Case attribute '{attr}': {sorted(df[attr].unique())}")
    for attr in variables.get('event_attributes', {}):
        print(f"Event attribute '{attr}': {sorted(df[attr].unique())}")

def test_ratios(df, variables, n_cases):
    print("\n=== RATIOS ===")
    # Deviation ratios
    deviations = {dev['name']: dev['probability'] for dev in variables.get('deviations', [])}
    case_deviations = {dev: set() for dev in deviations}
    for _, row in df.iterrows():
        case = row['case:concept:name']
        act = row['Activity']
        if act in deviations:
            case_deviations[act].add(case)
    for dev, prob in deviations.items():
        actual = len(case_deviations[dev])
        expected = int(round(prob * n_cases))
        print(f"Deviation '{dev}': actual={actual}, expected={expected}, ratio={actual/n_cases:.2f}")
    # Variant ratios
    variant_defs = {v['name']: v['sequence'] for v in variables.get('variants', [])}
    case_variants = Counter()
    for case in df['case:concept:name'].unique():
        acts = df[df['case:concept:name'] == case]['Activity'].tolist()
        for vname, vacts in variant_defs.items():
            idx = 0
            for act in acts:
                if idx < len(vacts) and act == vacts[idx]:
                    idx += 1
            if idx == len(vacts):
                case_variants[vname] += 1
                break
    for v, count in case_variants.items():
        freq = next((var['frequency'] for var in variables.get('variants', []) if var['name'] == v), None)
        expected = int(round(freq * n_cases)) if freq is not None else None
        print(f"Variant '{v}': actual={count}, expected={expected}, ratio={count/n_cases:.2f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='synthetic_event_log.csv')
    parser.add_argument('--variables', default='variables.txt')
    parser.add_argument('--n-cases', type=int, default=1000)
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--ratios', action='store_true')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    with open(args.variables, 'r', encoding='utf-8') as f:
        variables = yaml.safe_load(f)

    if args.all or args.strict:
        strict_test(df, variables)
    if args.all or args.summary:
        analyze_summary(df, variables)
    if args.all or args.ratios:
        test_ratios(df, variables, args.n_cases)

if __name__ == '__main__':
    main()
