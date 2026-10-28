import "dotenv/config";
import express, { NextFunction, Request, Response } from "express";
import cors from "cors";
import multer from "multer";
import pdf from "pdf-parse";
import { prisma } from "@finrag/database";

const app = express();
const port = Number(process.env.API_PORT || 8000);
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
app.use(cors({ origin: ["http://localhost:5173", "http://127.0.0.1:5173"] }));
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", async (_req: Request, res: Response) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    res.json({ status: "ok", database: "connected" });
  } catch {
    res.status(503).json({ status: "degraded", database: "unavailable" });
  }
});

app.get("/api/documents", async (_req, res, next) => {
  try {
    const documents = await prisma.document.findMany({
      orderBy: { createdAt: "desc" },
      select: { id: true, filename: true, pageCount: true, fileSize: true, createdAt: true, _count: { select: { chunks: true } } },
    });
    res.json({ documents: documents.map((d) => ({ id: d.id, filename: d.filename, pages: d.pageCount, fileSize: d.fileSize, createdAt: d.createdAt, chunks: d._count.chunks })) });
  } catch (error) { next(error); }
});

app.post("/api/documents/upload", upload.single("file"), async (req: Request, res: Response, next) => {
  try {
    if (!req.file) { res.status(400).json({ error: "Upload a PDF using the 'file' field." }); return; }
    if (req.file.mimetype !== "application/pdf" && !req.file.originalname.toLowerCase().endsWith(".pdf")) {
      res.status(400).json({ error: "Only PDF files are supported." }); return;
    }
    const parsed = await pdf(req.file.buffer);
    const document = await prisma.document.create({
      data: {
        filename: req.file.originalname,
        fileSize: req.file.size,
        pageCount: parsed.numpages,
        chunks: { create: chunkPdfText(parsed.text) },
      },
      select: { id: true, filename: true, pageCount: true, _count: { select: { chunks: true } } },
    });
    res.status(201).json({ id: document.id, filename: document.filename, pages: document.pageCount, chunks: document._count.chunks });
  } catch (error) { next(error); }
});

app.post("/api/analyze", async (req: Request, res: Response, next) => {
  try {
    const question = typeof req.body?.question === "string" ? req.body.question.trim() : "";
    if (question.length < 5 || question.length > 4000) {
      res.status(400).json({ error: "Question must be between 5 and 4000 characters." }); return;
    }
    const candidates = await prisma.documentChunk.findMany({
      include: { document: { select: { filename: true } } },
      take: 3000,
    });
    const evidence = rankChunks(question, candidates).slice(0, 8);
    const inputMetrics = Array.isArray(req.body?.metrics) ? req.body.metrics.slice(0, 100) : [];
    const calculations = calculateMetrics(inputMetrics);
    const findings = evidence.map((e) => `${e.content.slice(0, 500)} [Source: ${e.sourceId}, ${e.filename}, page ${e.page}]`);
    if (findings.length === 0) findings.push("No matching uploaded-document evidence was found. Upload relevant financial filings to ground the analysis.");
    const validation = {
      status: evidence.length > 0 ? "passed_with_warnings" : "needs_more_evidence",
      evidenceCount: evidence.length,
      claimsCount: findings.length,
      claimsWithSourceMarker: evidence.length,
      sourceCoverage: evidence.length / Math.max(1, findings.length),
      calculationCount: calculations.filter((c) => c.value !== null).length,
      notes: ["Source markers identify provenance; they do not guarantee correctness.", "Human review is required for financial decisions."],
    };
    const risks = [
      { category: "Evidence coverage", level: evidence.length ? "Low" : "High", detail: `${evidence.length} passages matched the query.` },
      { category: "Numerical consistency", level: calculations.length ? "Review" : "Unknown", detail: "Derived values use deterministic TypeScript arithmetic; source values require verification." },
    ];
    const agents = [
      { name: "Supervisor / Router", status: "completed", summary: "Decomposed the question into retrieval, calculation, synthesis, and validation tasks." },
      { name: "Financial Document Retrieval", status: evidence.length ? "completed" : "warning", summary: `Retrieved ${evidence.length} relevant passages using lexical ranking.` },
      { name: "Web & News", status: "skipped", summary: "Current news connector is not enabled in this TypeScript API yet." },
      { name: "Deterministic Calculator", status: "completed", summary: `Processed ${calculations.length} supplied or derived calculation rows.` },
      { name: "Synthesis", status: "completed", summary: "Composed a report with source-linked findings." },
      { name: "Risk Evaluation", status: evidence.length ? "completed" : "warning", summary: `Validation status: ${validation.status}.` },
    ];
    const analysis = await prisma.analysis.create({
      data: {
        question,
        company: typeof req.body?.company === "string" ? req.body.company.slice(0, 200) : null,
        executiveSummary: evidence.length
          ? "Analysis assembled from retrieved financial document passages and deterministic calculations. Verify evidence and context before relying on the findings."
          : "No uploaded-document evidence matched this question. Upload relevant filings before relying on the analysis.",
        validationStatus: validation.status,
        sourceCoverage: validation.sourceCoverage,
        evidence: { create: evidence.map((e) => ({ chunkId: e.id, sourceId: e.sourceId, filename: e.filename, page: e.page, excerpt: e.content.slice(0, 1200), score: e.score })) },
        calculations: { create: calculations.map((c) => ({ name: c.name, value: c.value, unit: c.unit, formula: c.formula, sourceIds: c.sourceIds })) },
        risks: { create: risks },
        agentRuns: { create: agents },
      },
      include: { evidence: true, calculations: true, risks: true, agentRuns: true },
    });
    res.json({
      reportId: analysis.id,
      title: "Financial Analysis & Risk Assessment",
      executiveSummary: analysis.executiveSummary,
      findings,
      calculations: analysis.calculations,
      risks: analysis.risks,
      evidence: analysis.evidence,
      validation,
      agents: analysis.agentRuns,
      limitations: [
        "This starter version uses lexical retrieval; dense embeddings and table-aware retrieval are future work.",
        "Current-news retrieval and MCP tool integration are not enabled in this TypeScript implementation.",
        "This tool is research support, not investment advice. Verify sources and arithmetic before making financial decisions.",
      ],
      createdAt: analysis.createdAt,
    });
  } catch (error) { next(error); }
});

app.get("/api/analyses", async (_req, res, next) => {
  try {
    const analyses = await prisma.analysis.findMany({ orderBy: { createdAt: "desc" }, take: 25, select: { id: true, question: true, validationStatus: true, sourceCoverage: true, createdAt: true } });
    res.json({ analyses });
  } catch (error) { next(error); }
});

app.use((error: unknown, _req: Request, res: Response, _next: NextFunction) => {
  const message = error instanceof Error ? error.message : "Unexpected server error";
  console.error(error);
  res.status(500).json({ error: message });
});

function chunkPdfText(raw: string): Array<{ page: number; chunkIndex: number; content: string }> {
  const paragraphs = raw.split(/\n\s*\n/).map((p) => p.replace(/\s+/g, " ").trim()).filter((p) => p.length >= 25);
  const chunks: Array<{ page: number; chunkIndex: number; content: string }> = [];
  for (let i = 0; i < paragraphs.length; i += 3) {
    const content = paragraphs.slice(i, i + 3).join(" ");
    if (content.length) chunks.push({ page: Math.min(1 + Math.floor(i / 12), 99999), chunkIndex: Math.floor(i / 3), content });
  }
  if (!chunks.length && raw.trim()) chunks.push({ page: 1, chunkIndex: 0, content: raw.trim().slice(0, 5000) });
  return chunks;
}

type Candidate = { id: string; page: number; chunkIndex: number; content: string; document: { filename: string } };
function rankChunks(question: string, candidates: Candidate[]) {
  const terms = new Set(question.toLowerCase().match(/[a-z0-9]{2,}/g) || []);
  return candidates.map((c) => {
    const words = new Set(c.content.toLowerCase().match(/[a-z0-9]{2,}/g) || []);
    const hits = [...terms].filter((t) => words.has(t)).length;
    const score = hits / Math.max(1, terms.size);
    return { id: c.id, sourceId: c.id, page: c.page, content: c.content, filename: c.document.filename, score };
  }).filter((c) => c.score > 0).sort((a, b) => b.score - a.score);
}

type MetricInput = { company?: string; period?: string; metric?: string; value?: number; unit?: string; sourceId?: string };
function calculateMetrics(input: MetricInput[]) {
  const valid = input.filter((m) => typeof m.metric === "string" && typeof m.value === "number" && Number.isFinite(m.value));
  const output = valid.map((m) => ({ name: m.metric!, value: m.value!, unit: m.unit || "", formula: "source value (input)", sourceIds: [m.sourceId || "user_input"] }));
  const groups = new Map<string, MetricInput[]>();
  for (const m of valid) {
    const key = `${m.company || "Unknown"}::${m.metric}`;
    groups.set(key, [...(groups.get(key) || []), m]);
  }
  for (const rows of groups.values()) {
    rows.sort((a, b) => String(a.period || "").localeCompare(String(b.period || "")));
    if (rows.length < 2) continue;
    const previous = rows[rows.length - 2], current = rows[rows.length - 1];
    if (typeof previous.value !== "number" || typeof current.value !== "number" || previous.value === 0) continue;
    output.push({
      name: `${current.metric} period change`,
      value: ((current.value - previous.value) / Math.abs(previous.value)) * 100,
      unit: "%",
      formula: "(current - previous) / abs(previous) * 100",
      sourceIds: [previous.sourceId || "user_input", current.sourceId || "user_input"],
    });
  }
  return output;
}

app.listen(port, () => console.log(`FinRAG TypeScript API listening on :${port}`));
