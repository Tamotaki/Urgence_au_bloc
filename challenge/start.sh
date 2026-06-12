#!/bin/bash

# 1. Run the challenge generator to populate /var/log/apache2/access.log, /tmp/backup.xor, etc.
python3 /app/files/generate_challenge.py

# Ensure correct permissions for the log files so that 'operateur' can read them
chmod 755 /var/log/apache2
chmod 644 /var/log/apache2/access.log
chmod 644 /var/log/apache2/error.log

# Copy ransomware_fake to /tmp just to be absolutely sure it's there
cp /app/files/ransomware_fake.py /tmp/ransomware_fake.py
chmod 755 /tmp/ransomware_fake.py

# 2. Start SSH daemon
/usr/sbin/sshd

# 3. Start ttyd listening on localhost:7681, running bash as 'attacker'
# We use su - attacker so the shell drops privileges to the attacker user
ttyd -p 7681 -b /terminal -i 127.0.0.1 su - attacker &

# 4. Start the Flask application
python3 /app/web/app.py &

# Wait for Flask to start listening on port 5000 before launching Nginx to avoid 502 Bad Gateway
until curl -s http://127.0.0.1:5000/ > /dev/null; do
  sleep 0.1
done

# 5. Start Nginx in foreground to keep container running
nginx -g "daemon off;"

