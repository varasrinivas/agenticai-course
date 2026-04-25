FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command runs the coordinator
CMD ["python", "coordinator.py", "--data-dir", "/data/mock_data"]
