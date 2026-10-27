def validate(evidence: list[dict], findings: list[str], calculations: list[dict], max_retries: int = 1) -> dict:
    cited = sum(1 for f in findings if '[Source:' in f)
    claim_count = len(findings)
    numeric_calcs = [c for c in calculations if c.get('value') is not None]
    return {
        'status': 'passed_with_warnings' if evidence and cited == claim_count else 'needs_more_evidence',
        'evidence_count': len(evidence), 'claims_count': claim_count,
        'claims_with_source_marker': cited,
        'source_coverage': round(cited / max(1, claim_count), 3),
        'calculation_count': len(numeric_calcs),
        'unsupported_claims_detected': max(0, claim_count-cited),
        'retry_limit': max_retries,
        'notes': ['Source markers indicate provenance, not proof that a claim is correct.', 'A human should verify important financial conclusions.']
    }
