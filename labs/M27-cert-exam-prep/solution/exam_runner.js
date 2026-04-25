/**
 * M27 Lab — Exercise 3 SOLUTION: Exam Runner
 * ============================================
 * Load and run mock exams from JSON files. Present questions, accept
 * answers (auto-answer mode for demo), score the exam, and show explanations.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function loadExam(filepath) {
  if (!fs.existsSync(filepath)) {
    throw new Error(`Exam file not found: ${filepath}`);
  }

  const raw = fs.readFileSync(filepath, "utf-8");
  const exam = JSON.parse(raw);

  const required = ["exam_id", "questions", "passing_score"];
  for (const field of required) {
    if (!(field in exam)) {
      throw new Error(`Exam file missing required field: ${field}`);
    }
  }

  if (exam.questions.length === 0) {
    throw new Error("Exam has no questions");
  }

  return exam;
}

function presentQuestion(question, index, total) {
  console.log(`\n  Question ${index + 1}/${total}`);
  console.log(
    `  ID: ${question.id} | Domain: ${question.domain_name} | ` +
      `Difficulty: ${question.difficulty}`
  );
  console.log(`  ${"-".repeat(50)}`);
  console.log(`  ${question.question}`);
  console.log();

  for (const letter of ["A", "B", "C", "D"]) {
    console.log(`    ${letter}) ${question.options[letter]}`);
  }

  const answer = question.correct_answer;
  console.log(`\n  > Auto-answer: ${answer}`);
  return answer;
}

function presentQuestionWrong(question, index, total) {
  console.log(`\n  Question ${index + 1}/${total}`);
  console.log(
    `  ID: ${question.id} | Domain: ${question.domain_name} | ` +
      `Difficulty: ${question.difficulty}`
  );
  console.log(`  ${"-".repeat(50)}`);
  console.log(`  ${question.question}`);
  console.log();

  for (const letter of ["A", "B", "C", "D"]) {
    console.log(`    ${letter}) ${question.options[letter]}`);
  }

  const correct = question.correct_answer;
  const wrong = ["A", "B", "C", "D"].filter((l) => l !== correct)[0];
  console.log(`\n  > Auto-answer: ${wrong} (intentionally wrong for demo)`);
  return wrong;
}

function scoreExam(questions, answers) {
  const total = questions.length;
  let correctCount = 0;
  const perQuestion = [];
  const domainScores = {};

  for (const q of questions) {
    const userAnswer = answers[q.id] || "";
    const isCorrect = userAnswer === q.correct_answer;

    if (isCorrect) correctCount++;

    perQuestion.push({
      id: q.id,
      userAnswer,
      correctAnswer: q.correct_answer,
      isCorrect,
      domain: q.domain,
      domainName: q.domain_name,
      questionSummary: q.question.substring(0, 60) + "...",
    });

    if (!domainScores[q.domain]) {
      domainScores[q.domain] = {
        name: q.domain_name,
        correct: 0,
        total: 0,
      };
    }
    domainScores[q.domain].total++;
    if (isCorrect) domainScores[q.domain].correct++;
  }

  const percentage = total > 0 ? (correctCount / total) * 100 : 0;

  return {
    total,
    correct: correctCount,
    percentage,
    perQuestion,
    domainScores,
  };
}

function showResults(exam, results) {
  const lines = [];
  const passing = exam.passing_score;
  const passed = results.percentage >= passing;

  lines.push("=".repeat(40));
  lines.push(`${exam.title} — Results`);
  lines.push("=".repeat(40));
  lines.push(
    `Score: ${results.correct}/${results.total} ` +
      `(${Math.round(results.percentage)}%)`
  );
  lines.push(
    `Status: ${passed ? "PASSED" : "FAILED"} (passing: ${passing}%)`
  );
  lines.push("");

  lines.push("Per-Domain Breakdown:");
  for (const domainNum of Object.keys(results.domainScores).sort()) {
    const ds = results.domainScores[domainNum];
    const pct = ds.total > 0 ? (ds.correct / ds.total) * 100 : 0;
    const check = pct >= passing ? "+" : "-";
    lines.push(
      `  Domain ${domainNum} (${ds.name}):  ` +
        `${ds.correct}/${ds.total} — ${Math.round(pct)}% ${check}`
    );
  }
  lines.push("");

  lines.push("Questions:");
  for (const pq of results.perQuestion) {
    const mark = pq.isCorrect ? "+" : "X";
    lines.push(
      `  ${pq.id}: ${mark} (${pq.userAnswer}) — ${pq.questionSummary}`
    );
  }
  lines.push("");

  const weakDomains = [];
  for (const [domainNum, ds] of Object.entries(results.domainScores)) {
    const pct = ds.total > 0 ? (ds.correct / ds.total) * 100 : 0;
    if (pct < 80) weakDomains.push(`Domain ${domainNum}`);
  }

  if (weakDomains.length > 0) {
    lines.push(
      `Weak Areas: ${weakDomains.join(", ")} — Review related modules`
    );
  } else {
    lines.push("Weak Areas: None — all domains above 80%");
  }

  const output = lines.join("\n");
  console.log(output);
  return output;
}

function runExam(filepath, wrongIndices = []) {
  const exam = loadExam(filepath);
  const questions = exam.questions;
  const answers = {};

  console.log(`\n${"=".repeat(56)}`);
  console.log(`  ${exam.title}`);
  console.log(`  ${exam.description}`);
  console.log(
    `  Questions: ${questions.length} | Passing: ${exam.passing_score}% | ` +
      `Time: ${exam.time_limit_minutes} min`
  );
  console.log("=".repeat(56));

  for (let i = 0; i < questions.length; i++) {
    const question = questions[i];
    let answer;
    if (wrongIndices.includes(i)) {
      answer = presentQuestionWrong(question, i, questions.length);
    } else {
      answer = presentQuestion(question, i, questions.length);
    }
    answers[question.id] = answer;
  }

  console.log(`\n${"=".repeat(56)}`);
  console.log("  Scoring...");
  console.log(`${"=".repeat(56)}\n`);

  const results = scoreExam(questions, answers);
  showResults(exam, results);

  return {
    examId: exam.exam_id,
    questions,
    answers,
    results,
  };
}

function main() {
  let filepath;
  if (process.argv.length < 3) {
    const examDir = path.join(__dirname, "..", "mock_exams");
    filepath = path.join(examDir, "exam_a.json");
  } else {
    filepath = process.argv[2];
  }

  console.log(`Loading exam from: ${filepath}`);
  console.log(
    "(Auto-answer mode: demonstrating with correct answers, 1 wrong for demo)\n"
  );

  // Get 9/10 correct (miss question index 2 for demo)
  runExam(filepath, [2]);
}

main();
