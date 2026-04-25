/**
 * M22B: AWS Lambda Handler (Node.js Solution)
 * ==============================================
 * Adapts the Express app for AWS Lambda using serverless-http.
 *
 * serverless-http is the Node.js equivalent of Python's Mangum —
 * it wraps an Express/Koa/etc. app so Lambda can invoke it.
 */

const serverless = require("serverless-http");
const app = require("./server");

module.exports.handler = serverless(app);
