def calculate_metrics(metrics: list[dict]) -> list[dict]:
    """Only deterministic Python arithmetic. Metrics must be supplied/extracted values."""
    out = []
    for metric in metrics:
        out.append({'name': metric.get('metric','Metric'), 'value': metric.get('value'), 'unit': metric.get('unit',''), 'formula': 'source value (no derived calculation)', 'source_id': metric.get('source_id','user_input')})
    grouped = {}
    for m in metrics: grouped.setdefault((m.get('company','Unknown'),m.get('metric','Metric')), []).append(m)
    for (company,name), rows in grouped.items():
        rows = sorted(rows, key=lambda x: x.get('period',''))
        if len(rows) >= 2:
            old, new = rows[-2], rows[-1]
            base, current = float(old['value']), float(new['value'])
            growth = None if base == 0 else ((current-base)/abs(base))*100
            out.append({'name': f'{name} period change', 'company': company, 'from_period': old.get('period'), 'to_period': new.get('period'), 'previous_value': base, 'current_value': current, 'value': growth, 'unit': '%', 'formula': '(current - previous) / abs(previous) * 100', 'source_id': f"{old.get('source_id','user_input')}, {new.get('source_id','user_input')}"})
    return out
