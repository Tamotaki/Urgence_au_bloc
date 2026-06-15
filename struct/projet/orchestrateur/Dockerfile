FROM python:3.12-slim

# Install Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Configure Nginx
COPY nginx.conf /etc/nginx/sites-available/default

# Configure startup script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5000
CMD ["./start.sh"]