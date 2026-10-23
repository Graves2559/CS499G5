
# 
FROM python:3.11-slim

WORKDIR /app

# lsof is needed by kill_process_on_port(); not included in the slim base image
RUN apt-get update && apt-get install -y --no-install-recommends lsof \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Must do this to ensure that the logs (in Docker) actually tell you the tunneling service's public URL
ENV PYTHONUNBUFFERED=1  

CMD ["python", "main.py"]