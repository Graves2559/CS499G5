#
FROM python:3.11-slim

WORKDIR /app



# lsof is needed by kill_process_on_port(); not included in the slim base image
RUN apt-get update && apt-get install -y --no-install-recommends lsof \
    && rm -rf /var/lib/apt/lists/*

COPY backend/WI29_Server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# The backend is a set of packages under /app/backend: CommonErrors (shared errors), UserLogin (accounts) and
# WI29_Server (files, sessions, HTTP). Each has domain / application / infrastructure layers.
COPY backend/CommonErrors ./backend/CommonErrors
COPY backend/UserLogin ./backend/UserLogin
COPY backend/WI29_Server ./backend/WI29_Server
COPY dist ./dist
ENV PYTHONPATH=/app/backend

# The private/free port here is the one used within the main.py of WI29_Server
EXPOSE 8000

# Must do this to ensure that the logs (in Docker) actually tell you the tunneling service's public URL
ENV PYTHONUNBUFFERED=1  

CMD ["python", "-m", "WI29_Server.main"]
