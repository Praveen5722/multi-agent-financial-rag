from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from uuid import uuid4
from .schemas import AnalyzeRequest, AnalyzeResponse, Evidence, AgentStatus
from .store import ingest_pdf, retrieve, list_documents
from .agents.supervisor import decompose
from .agents.calculator import calculate_metrics
from .agents.news import search_news
from .agents.synthesis import synthesize
from .agents.validator import validate

load_dotenv()
app = FastAPI(title='FinRAG Multi-Agent Financial Analysis API', version='1.0.0', description='Evidence-linked financial research with deterministic calculations and validation.')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.get('/api/health')
def health(): return {'status':'ok','service':'FinRAG API'}

@app.get('/api/documents')
def documents(): return {'documents': list_documents()}

@app.post('/api/documents/upload')
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, 'Please upload a PDF financial report.')
    data = await file.read()
    if len(data) > 25 * 1024 * 1024: raise HTTPException(413, 'Maximum PDF size is 25 MB.')
    try: return ingest_pdf(file.filename, data)
    except Exception as exc: raise HTTPException(400, f'Could not parse PDF: {exc}')

@app.post('/api/analyze', response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    plan = decompose(req.question)
    evidence = retrieve(req.question, 8)
    news = await search_news(req.question) if 'search_current_news' in plan['tasks'] else []
    calcs = calculate_metrics([m.model_dump() for m in req.metrics])
    report = synthesize(req.question, evidence, calcs, news)
    validation = validate(evidence, report['findings'], calcs)
    agents = [
      AgentStatus(name='Supervisor / Router', status='completed', summary=f"Decomposed query into {len(plan['tasks'])} tasks."),
      AgentStatus(name='Financial Document Retrieval', status='completed' if evidence else 'warning', summary=f"Retrieved {len(evidence)} relevant passages using lexical search."),
      AgentStatus(name='Web & News', status='completed' if news else ('skipped' if 'search_current_news' not in plan['tasks'] else 'warning'), summary=f"Returned {len(news)} news results. Configure TAVILY_API_KEY for current news."),
      AgentStatus(name='Deterministic Calculator', status='completed', summary=f"Processed {len(calcs)} metric inputs/derived values using Python arithmetic."),
      AgentStatus(name='Synthesis', status='completed', summary='Built an evidence-linked report from retrieved passages and tool outputs.'),
      AgentStatus(name='Risk Evaluation', status='completed' if validation['status']=='passed_with_warnings' else 'warning', summary=f"Validation status: {validation['status']}.")]
    limitations = []
    if not evidence: limitations.append('No matching source passages were found. Upload company filings or reports before relying on this analysis.')
    if not news and 'search_current_news' in plan['tasks']: limitations.append('Current news was not retrieved. Configure TAVILY_API_KEY in backend/.env.')
    limitations += ['This starter implementation uses lexical retrieval; dense embeddings and table-aware retrieval can be added for stronger recall.', 'This tool provides research support, not investment advice. Verify source documents and calculations before making financial decisions.']
    return AnalyzeResponse(report_id=str(uuid4()), title='Financial Analysis & Risk Assessment', executive_summary=report['executive_summary'], findings=report['findings'], calculations=report['calculations'], risks=[{'category':'Evidence coverage','level':'Low' if evidence else 'High','detail':f"{len(evidence)} passages matched the query."},{'category':'Current information','level':'Medium' if news else 'Unknown','detail':f"{len(news)} current-news items retrieved."},{'category':'Numerical consistency','level':'Review','detail':'Derived values are calculated by Python; supplied input values still need source verification.'}], evidence=[Evidence(**e) for e in evidence], validation=validation, agents=agents, limitations=limitations)
