FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure backup and data directory exists
RUN mkdir -p backups

# Expose port
EXPOSE 8000

# Run both Web & Telegram bot service
CMD ["python", "main.py"]
