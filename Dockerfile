# 1. Start with python
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first (for caching efficiency)
COPY requirements.txt .

# 4. Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Expose the port the app listens on
EXPOSE 5000

ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1

# Single worker: SQLite is not safe across multiple processes.
# Timeout is raised so slower LLM reviews can finish.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "1", "--timeout", "120", "main:app"]
