import hmac
import hashlib
import os
import subprocess
import logging
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Secret key for GitHub webhook (should be set in environment variables)
WEBHOOK_SECRET = settings.GITHUB_WEBHOOK_SECRET

async def verify_signature(request: Request):
    """Verify that the webhook is from GitHub"""
    if not WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET not set, skipping signature verification")
        return True
        
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        raise HTTPException(status_code=403, detail="X-Hub-Signature-256 header missing")
        
    payload = await request.body()
    calculated_signature = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(calculated_signature, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
        
    return True


async def run_deployment(background_tasks: BackgroundTasks):
    """Run the deployment script in the background"""
    def execute_deploy_script():
        try:
            # Make the script executable
            os.chmod("deploy.sh", 0o755)
            # Run the deployment script
            result = subprocess.run(["./deploy.sh"], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            logger.info(f"Deployment successful: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Error during deployment: {str(e)}")
    
    background_tasks.add_task(execute_deploy_script)


@router.post("/github-webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_signature)
):
    """Handle GitHub webhook events"""
    event_type = request.headers.get('X-GitHub-Event')
    payload = await request.json()
    
    # Only process push events to the main branch
    if event_type == "push" and payload.get("ref") == "refs/heads/main":
        logger.info("Received push event to main branch, triggering deployment")
        await run_deployment(background_tasks)
        return {"status": "Deployment triggered"}
    
    return {"status": "No action taken"}
