from fastapi import APIRouter, Body
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from functions.email import send_email
from functions.sms import send_sms


router = APIRouter(
    prefix='/portfolio',
    tags=['portfolio']
)

load_dotenv()

TWILIO_PHONE = os.getenv('TWILIO_PHONE')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH = os.getenv('TWILIO_AUTH')

TWILIO_PHONE2 = os.getenv('TWILIO_PHONE2')
TWILIO_SID2 = os.getenv('TWILIO_SID2')
TWILIO_AUTH2 = os.getenv('TWILIO_AUTH2')

MY_EMAIL = os.getenv('MY_EMAIL')
PASSWORD = os.getenv('PASSWORD')


class EmailData(BaseModel):
    full_name: str
    email: str
    phone: str
    subject: str
    msg: str


@router.put('/email_sender')
async def email_sender(data: EmailData = Body(...)):
    try:
        full_name = data.full_name
        email = data.email
        phone = data.phone
        subject = data.subject
        msg = data.msg
        new_msg = f'''
        hello {full_name},
        you've sent an email to Nitay Newman on the subject: {subject}.
        Your phone number: {phone}
        Your email: {email}
        Message: {msg}
        '''
        await send_email(msg=new_msg, title="Nitay Newman Portfolio", src_email=MY_EMAIL, src_password=PASSWORD, dest_email=email)

        # await send_sms(msg=new_msg)
        return {"success": True}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False}
    

@router.put('/sms_sender')
async def sms_sender(msg):
    await send_sms(msg)