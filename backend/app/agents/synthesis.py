def synthesize(question: str, evidence: list[dict], calculations: list[dict], news: list[dict]) -> dict:
    findings = []
    for e in evidence:
        findings.append(f"{e['text'][:420]} [Source: {e['source_id']}, {e['filename']}, page {e.get('page','?')}]")
    for n in news:
        findings.append(f"{n.get('title','News item')}: {n.get('content','')} [Source: {n.get('source_id','')}]")
    if not findings: findings.append('No matching uploaded-document evidence was found. Upload relevant financial filings or reports to ground the analysis.')
    summary = 'Analysis assembled from retrieved document passages and deterministic calculations. ' + ('Evidence was found for review.' if evidence else 'No uploaded-document evidence matched this query.')
    return {'executive_summary': summary, 'findings': findings[:12], 'calculations': calculations}
