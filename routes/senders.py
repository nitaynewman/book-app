# routes/senders.py
from fastapi import APIRouter, Depends
from functions.email import send_email
from functions.sms import send_sms
import asyncio
from concurrent.futures import ThreadPoolExecutor
from helper.authentication import APIKeyChecker

router = APIRouter(
    prefix='/senders',
    tags=['senders']
)

executor = ThreadPoolExecutor(max_workers=3)

# Create dependency instances for different permissions
email_auth = APIKeyChecker("email")
sms_auth = APIKeyChecker("sms")


@router.put('/email_sender')
async def email_sender(
    src_email: str, 
    dest_email: str, 
    title: str, 
    message: str,
    api_key: str = Depends(email_auth)  # Requires "email" permission
):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            send_email, 
            src_email, 
            dest_email, 
            title, 
            message
        )
        
        if result.get("success"):
            return {"success": True, 'message': 'email sent successfully'}
        else:
            return {"success": False, 'message': f"email failed: {result.get('error')}"}
    except Exception as e:
        return {"success": False, 'message': f"email failed with this error: {e}"}


@router.put('/sms_sender')
async def sms_sender(
    msg: str, 
    dest: str,
    api_key: str = Depends(sms_auth)  # Requires "sms" permission
):
    try:
        await send_sms(msg, dest)
        return {"success": True, 'message': 'sms sent successfully'}
    except Exception as e:
        return {"success": False, 'message': f"sms failed with this error: {e}"}