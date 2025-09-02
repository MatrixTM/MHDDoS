# much smaller image than debian based python images
FROM python:3.12-slim

LABEL maintainer="0xkatana"

WORKDIR /app

# Install git 
RUN apt-get update && apt-get install -y git && apt-get clean

# copy requirements.txt for better caching 
COPY requirements.txt .

# Install py dependencies (may migrate to uv later)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code at once  instead of copy code then files 
COPY . .

ENTRYPOINT ["python", "start.py"]
