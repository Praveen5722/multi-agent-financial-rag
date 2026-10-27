def decompose(question: str) -> dict:
    q = question.lower()
    tasks = ['retrieve_financial_evidence', 'synthesize_findings', 'validate_report']
    if any(w in q for w in ['growth','ratio','margin','percentage','compare','change','calculate','revenue']):
        tasks.insert(1, 'calculate_metrics')
    if any(w in q for w in ['news','recent','latest','supply chain','geopolitical','regulatory','market risk']):
        tasks.insert(1, 'search_current_news')
    return {'question': question, 'tasks': tasks}
