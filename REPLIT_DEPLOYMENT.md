# Automatic Redeployment on Replit

This guide explains how to set up automatic redeployment on Replit when changes are pushed to your GitHub repository.

## Setup Instructions

### 1. Configure Replit

1. Make sure your project is already connected to your GitHub repository.

2. Add the following environment variable in your Replit project:
   - Go to the "Secrets" tab (lock icon) in the sidebar
   - Add a new secret with key `GITHUB_WEBHOOK_SECRET` and a secure random value
   - This will be used to verify that webhook requests are coming from GitHub

### 2. Set Up GitHub Webhook

1. Go to your GitHub repository (https://github.com/vishalsachdev/LearnByEmail)
2. Click on "Settings" > "Webhooks" > "Add webhook"
3. Configure the webhook:
   - Payload URL: `https://your-replit-app-url/webhooks/github-webhook`
   - Content type: `application/json`
   - Secret: Enter the same value you used for `GITHUB_WEBHOOK_SECRET` in Replit
   - Events: Select "Just the push event"
   - Active: Check this box
4. Click "Add webhook"

### 3. Test the Setup

1. Make a small change to your repository and push it to GitHub
2. Check the Replit console logs to see if the webhook was received and the deployment was triggered

## How It Works

1. When you push changes to your GitHub repository, GitHub sends a webhook to your Replit app
2. The webhook handler in your app verifies the request is from GitHub using the secret
3. If it's a push to the main branch, it runs the deployment script
4. The deployment script pulls the latest changes, runs migrations, and restarts the app

## Troubleshooting

- If the webhook isn't working, check the Replit logs for error messages
- Verify that your Replit app is awake and running (free Replit projects go to sleep after inactivity)
- Make sure the webhook URL is correct and accessible from the internet
- Check that the secret matches between GitHub and your Replit environment variable
