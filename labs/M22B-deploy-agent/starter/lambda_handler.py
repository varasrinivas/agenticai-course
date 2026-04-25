"""
M22B: AWS Lambda Handler (Starter — complete the TODOs)
=========================================================
Adapts the FastAPI application for AWS Lambda using Mangum.

Mangum is a library that converts API Gateway events into ASGI
requests that FastAPI can handle. It's the standard way to run
FastAPI on Lambda.

This file should be just 3 lines of real code when complete.
"""

# TODO 1: Import the Mangum adapter
# Mangum bridges AWS Lambda's event format with ASGI (FastAPI's protocol).
# from mangum import Mangum


# TODO 2: Import the FastAPI app from server.py
# from server import app


# TODO 3: Create the Lambda handler
# Mangum wraps the FastAPI app. AWS Lambda calls handler(event, context).
# lifespan="off" disables ASGI lifespan events (not needed on Lambda).
# handler = Mangum(app, lifespan="off")

# That's it! When Lambda receives a request:
#   1. API Gateway converts the HTTP request into a Lambda event
#   2. Mangum converts the Lambda event into an ASGI request
#   3. FastAPI processes the ASGI request normally
#   4. Mangum converts the ASGI response back to a Lambda response
#   5. API Gateway converts the Lambda response to HTTP
