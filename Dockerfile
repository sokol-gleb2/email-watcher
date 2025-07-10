FROM node:20

# Install Python 3.12
RUN apt-get update && \
    apt-get install -y wget build-essential libssl-dev zlib1g-dev \
    libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev \
    libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev && \
    cd /usr/src && \
    wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz && \
    tar xzf Python-3.12.3.tgz && \
    cd Python-3.12.3 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    ln -sf /usr/local/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip3

# Set working directory
WORKDIR /app

# Copy Node app
COPY server ./server
WORKDIR /app/server
RUN npm install

# Copy Python app
WORKDIR /app
COPY parser ./parser
RUN pip3 install -r parser/requirements.txt

# Set working directory back to Node app
WORKDIR /app/server

# Start Node app
CMD ["node", "emailAutomation.js"]