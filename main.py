from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import smtplib
import uvicorn
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
TWILIO_PHONE = os.getenv('TWILIO_PHONE')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH = os.getenv('TWILIO_AUTH')

MY_EMAIL = os.getenv('MY_EMAIL')
PASSWORD = os.getenv('PASSWORD')

app = FastAPI()

# CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the model for the email data
class EmailData(BaseModel):
    full_name: str
    email: str
    phone: str
    subject: str
    msg: str

@app.put('/email/')
def send_email(data: EmailData = Body(...)):
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

        connection = smtplib.SMTP("smtp.gmail.com", 587)
        print('first connection')
        connection.starttls()
        connection.login(user=MY_EMAIL, password=PASSWORD)
        print('loged in ')
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=[MY_EMAIL, email], 
            msg=f"Subject: {subject} to Nitay Newman\n\n{new_msg}"
        )
        print('sent mail')
        connection.close()
        send_sms(new_msg)
        print('sent sms')
        return {"success": True}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False}
    
def send_sms(msg):
    print('starting to send sms')
    client = Client(TWILIO_SID, TWILIO_AUTH)
    print('connected to client')
    message = client.messages.create(
        from_=TWILIO_PHONE,
        body=msg,
        to='+972584680232'
    )
    print('sent sms')
    print(f"send sms {message.sid}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
