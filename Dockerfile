# Use slim Python 3.12 base image
FROM python:3.12-slim

# Install Node.js 20 and basic dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Node.js app
COPY server ./server
WORKDIR /app/server
RUN npm install

# Copy and install Python app
WORKDIR /app
COPY parser ./parser
RUN pip install --no-cache-dir -r parser/requirements.txt

# Set working directory back to Node app
WORKDIR /app/server

# Start Node app
CMD ["node", "emailAutomation.js"]