import pandas as pd

def main():
    df = pd.read_csv('synthetic_event_log.csv')
    cases = df['case:concept:name'].unique()
    deviations = ['Late Payment', 'Order Change', 'Partial Shipment']
    deviation_counts = {dev: 0 for dev in deviations}
    for dev in deviations:
        # Count unique cases where this deviation appears as an activity
        cases_with_dev = df[df['Activity'] == dev]['case:concept:name'].unique()
        deviation_counts[dev] = len(cases_with_dev)
    print('Deviation frequencies (cases with deviation):')
    for dev, count in deviation_counts.items():
        print(f'  {dev}: {count}')

    # Variant distribution (by activity sequence)
    variant_defs = {
        'Standard': ['Receive Order', 'Check Credit', 'Approve Order', 'Pick Items', 'Pack Items', 'Ship Order', 'Send Invoice', 'Receive Payment'],
        'No Credit Check': ['Receive Order', 'Approve Order', 'Pick Items', 'Pack Items', 'Ship Order', 'Send Invoice', 'Receive Payment'],
        'Express': ['Receive Order', 'Pick Items', 'Pack Items', 'Ship Order', 'Send Invoice', 'Receive Payment']
    }
    variant_counts = {k: 0 for k in variant_defs}
    for case in cases:
        acts = df[df['case:concept:name'] == case]['Activity'].tolist()
        for vname, vacts in variant_defs.items():
            # Check if all variant activities are present in order (allow deviations in between)
            idx = 0
            for act in acts:
                if idx < len(vacts) and act == vacts[idx]:
                    idx += 1
            if idx == len(vacts):
                variant_counts[vname] += 1
                break
    print('\nVariant distribution (cases):')
    for v, count in variant_counts.items():
        print(f'  {v}: {count}')

    # Attribute value coverage
    print('\nAttribute value coverage:')
    for col in ['CustomerType', 'Region', 'Resource', 'Channel']:
        print(f'  {col}: {sorted(df[col].unique())}')

if __name__ == '__main__':
    main()
