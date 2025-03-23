#!/bin/bash

# Pull latest changes from GitHub
git pull origin main

# Run migrations if needed
python migration_email_confirmation.py

# Install any new dependencies
pip install -r requirements.txt

# Restart the application
# This will depend on how your app is configured to run on Replit
# The script will exit and Replit will restart the app automatically
exit 0
