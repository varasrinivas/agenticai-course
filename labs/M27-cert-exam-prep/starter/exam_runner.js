/**
 * M27 Lab — Exercise 3: Exam Runner
 * ==================================
 * Load and run mock exams from JSON files. Present questions, accept
 * answers, score the exam, and show explanations.
 *
 * YOUR TASK: Implement loadExam(), presentQuestion(), scoreExam(),
 * and showResults().
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Load a mock exam from a JSON file.
 *
 * TODO: Implement this function. It should:
 * 1. Read the JSON file
 * 2. Validate it has required fields (exam_id, questions, passing_score)
 * 3. Return the parsed exam object
 * 4. Throw an Error on invalid files
 */
function loadExam(filepath) {
  // YOUR CODE HERE
}

/**
 * Display a question and return the user's answer.
 *
 * TODO: Implement this function. It should:
 * 1. Print the question number, domain, and difficulty
 * 2. Print the question text
 * 3. Print all 4 options (A, B, C, D)
 * 4. Return the correct answer (auto-answer mode for demo)
 */
function presentQuestion(question, index, total) {
  // YOUR CODE HERE
}

/**
 * Score the exam and return results.
 *
 * TODO: Implement this function. It should:
 * 1. Compare answers to correct answers
 * 2. Calculate total score and percentage
 * 3. Calculate per-domain scores
 * 4. Return a results object with all scoring data
 */
function scoreExam(questions, answers) {
  // YOUR CODE HERE
}

/**
 * Display exam results and return formatted output.
 *
 * TODO: Implement this function. It should:
 * 1. Print overall score and pass/fail status
 * 2. Print per-domain breakdown
 * 3. Print per-question results with explanations
 * 4. Return the formatted output string
 */
function showResults(exam, results) {
  // YOUR CODE HERE
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
  console.log("(Auto-answer mode: demonstrating with correct answers)\n");

  // TODO: Load exam, run questions, score, show results
  console.log("Not yet implemented — complete the functions above!");
}

main();
