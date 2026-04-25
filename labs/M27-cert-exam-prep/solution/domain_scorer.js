/**
 * M27 Lab — Exercise 4 SOLUTION: Domain Scorer
 * ==============================================
 * Score exam results by domain, identify weak areas, and generate
 * study recommendations.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DOMAINS = {
  1: {
    name: "Agentic Architecture",
    weight: 25,
    modules: ["M12", "M13", "M14", "M26"],
  },
  2: {
    name: "Tool Design & MCP",
    weight: 20,
    modules: ["M05", "M06", "M07"],
  },
  3: {
    name: "Claude Code Configuration",
    weight: 20,
    modules: ["M25", "M26"],
  },
  4: {
    name: "Prompt Engineering & Structured Output",
    weight: 15,
    modules: ["M03", "M04", "M16", "M17"],
  },
  5: {
    name: "Context & Reliability",
    weight: 20,
    modules: ["M08", "M11", "M18", "M19"],
  },
};

// Simulated exam results for demo purposes
const SIMULATED_RESULTS = {
  mock_exam_a: {
    wrongIds: ["A3"],
  },
  mock_exam_b: {
    wrongIds: [],
  },
  mock_exam_c: {
    wrongIds: ["C2", "C9"],
  },
};

function loadExamResults(examDir) {
  const results = [];

  const files = fs
    .readdirSync(examDir)
    .filter((f) => f.startsWith("exam_") && f.endsWith(".json"))
    .sort();

  if (files.length === 0) {
    throw new Error(`No exam files found in ${examDir}`);
  }

  for (const file of files) {
    const filepath = path.join(examDir, file);
    const raw = fs.readFileSync(filepath, "utf-8");
    const exam = JSON.parse(raw);

    const examId = exam.exam_id;
    const sim = SIMULATED_RESULTS[examId] || { wrongIds: [] };
    const wrongIds = new Set(sim.wrongIds);

    const questionResults = [];
    for (const q of exam.questions) {
      questionResults.push({
        id: q.id,
        domain: q.domain,
        domainName: q.domain_name,
        difficulty: q.difficulty,
        isCorrect: !wrongIds.has(q.id),
        correctAnswer: q.correct_answer,
      });
    }

    results.push({
      examId,
      title: exam.title,
      questions: questionResults,
    });
  }

  return results;
}

function calculateDomainScores(results) {
  const domainScores = {};

  for (const examResult of results) {
    for (const q of examResult.questions) {
      const domain = q.domain;
      if (!domainScores[domain]) {
        domainScores[domain] = {
          name: q.domainName,
          correct: 0,
          total: 0,
          weight: (DOMAINS[domain] || {}).weight || 0,
          modules: (DOMAINS[domain] || {}).modules || [],
        };
      }
      domainScores[domain].total++;
      if (q.isCorrect) domainScores[domain].correct++;
    }
  }

  for (const domain in domainScores) {
    const ds = domainScores[domain];
    ds.percentage = ds.total > 0 ? (ds.correct / ds.total) * 100 : 0;
  }

  return domainScores;
}

function identifyWeakAreas(domainScores, threshold = 80.0) {
  const weakAreas = [];

  for (const domainNum of Object.keys(domainScores)
    .map(Number)
    .sort((a, b) => a - b)) {
    const ds = domainScores[domainNum];
    if (ds.percentage < threshold) {
      weakAreas.push({
        domain: domainNum,
        name: ds.name,
        percentage: ds.percentage,
        modules: ds.modules,
      });
    }
  }

  return weakAreas;
}

function generateReport(domainScores, weakAreas) {
  const lines = [];

  let totalCorrect = 0;
  let totalQuestions = 0;
  for (const ds of Object.values(domainScores)) {
    totalCorrect += ds.correct;
    totalQuestions += ds.total;
  }
  const overallPct =
    totalQuestions > 0 ? (totalCorrect / totalQuestions) * 100 : 0;
  const estimatedScore = Math.round(overallPct * 10);

  let recommendation;
  if (overallPct >= 85) {
    recommendation = "READY for certification exam";
  } else if (overallPct >= 72) {
    recommendation = "NEEDS REVIEW — close to passing, address weak areas";
  } else {
    recommendation = "NOT READY — significant preparation needed";
  }

  lines.push("=".repeat(40));
  lines.push("Certification Readiness Report");
  lines.push("=".repeat(40));
  lines.push(
    `Combined Score: ${totalCorrect}/${totalQuestions} (${Math.round(overallPct)}%)`
  );
  lines.push(`Estimated Exam Score: ~${estimatedScore}/1000`);
  lines.push("");

  lines.push("Domain Breakdown:");
  let bestDomain = null;
  let bestPct = -1;
  let worstDomain = null;
  let worstPct = 101;

  for (const domainNum of Object.keys(domainScores)
    .map(Number)
    .sort((a, b) => a - b)) {
    const ds = domainScores[domainNum];
    const pct = ds.percentage;
    const check = pct >= 72 ? "+" : "-";
    lines.push(
      `  Domain ${domainNum} — ${ds.name} (${ds.weight}%):  ` +
        `${Math.round(pct)}% ${check}`
    );

    if (pct > bestPct) {
      bestPct = pct;
      bestDomain = [domainNum, ds.name];
    }
    if (pct < worstPct) {
      worstPct = pct;
      worstDomain = [domainNum, ds.name];
    }
  }

  lines.push("");
  lines.push(`Recommendation: ${recommendation}`);

  if (bestDomain) {
    lines.push(`Strongest: Domain ${bestDomain[0]} (${bestDomain[1]})`);
  }
  if (worstDomain) {
    const modules = (domainScores[worstDomain[0]].modules || []).join(", ");
    lines.push(
      `Weakest: Domain ${worstDomain[0]} (${worstDomain[1]}) — Review ${modules}`
    );
  }

  if (weakAreas.length > 0) {
    lines.push("");
    lines.push("Study Plan for Weak Areas:");
    for (const wa of weakAreas) {
      const modules = wa.modules.join(", ");
      lines.push(
        `  Domain ${wa.domain} (${wa.name}): ` +
          `${Math.round(wa.percentage)}% — Review ${modules}`
      );
    }
  }

  const output = lines.join("\n");
  console.log(output);
  return output;
}

function main() {
  const examDir = path.join(__dirname, "..", "mock_exams");
  console.log(`Loading exams from: ${examDir}`);
  console.log("(Demo mode: using simulated answers)\n");

  const results = loadExamResults(examDir);
  console.log(`Loaded ${results.length} exam(s)\n`);

  const domainScores = calculateDomainScores(results);
  const weakAreas = identifyWeakAreas(domainScores);
  generateReport(domainScores, weakAreas);
}

main();
