"""
M22B: AWS Lambda Handler (Solution)
======================================
Adapts the FastAPI application for AWS Lambda using Mangum.
"""

from mangum import Mangum
from server import app

handler = Mangum(app, lifespan="off")
