FROM python:3.10-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    openssh-server \
    sudo \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd static binary from GitHub based on CPU architecture (supporting Apple Silicon and Intel)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -Lo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        curl -Lo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.aarch64; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    chmod +x /usr/local/bin/ttyd

# Configure SSH
RUN mkdir -p /var/run/sshd
RUN echo "UseDNS no" >> /etc/ssh/sshd_config
RUN useradd -m -s /bin/bash operateur && echo "operateur:Hopital2024" | chpasswd
RUN useradd -m -s /bin/bash attacker && echo "attacker:attacker" | chpasswd

# Setup directory
WORKDIR /app

# Copy requirements and install
COPY web/requirements.txt ./web/requirements.txt
RUN pip install --no-cache-dir -r ./web/requirements.txt

# Copy challenge files
COPY . .

# Setup files
RUN cp files/ransomware_fake.py /tmp/ransomware_fake.py && chmod +x /tmp/ransomware_fake.py
COPY files/motd.txt /etc/motd

# Configure Nginx
COPY nginx.conf /etc/nginx/sites-available/default

# Configure start script
RUN chmod +x start.sh

EXPOSE 80
CMD ["/app/start.sh"]
