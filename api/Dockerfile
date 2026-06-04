FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy api code into /app/api/ so "from api.xxx" imports resolve
COPY . ./api/

# Add both /app (for "from api.xxx") and /app/api (for "from utils.xxx") to PYTHONPATH
ENV PYTHONPATH="/app:/app/api"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
