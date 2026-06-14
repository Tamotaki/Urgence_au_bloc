#!/bin/bash

# Start the Flask app in the background
python app.py &

# Start Nginx in the foreground to keep the container running
nginx -g "daemon off;"
