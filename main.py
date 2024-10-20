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

TWILIO_PHONE2 = os.getenv('TWILIO_PHONE2')
TWILIO_SID2 = os.getenv('TWILIO_SID2')
TWILIO_AUTH2 = os.getenv('TWILIO_AUTH2')

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
    print('Starting to send SMS...')
    
    try:
        # First attempt with the primary Twilio account
        client = Client(TWILIO_SID, TWILIO_AUTH)
        print('Connected to primary Twilio client')
        
        message = client.messages.create(
            from_=TWILIO_PHONE,
            body=msg,
            to='+972584680232'
        )
        print('Sent SMS from primary account')
        
    except Exception as e1:
        # If the first Twilio account fails, try the second one
        print(f"Primary Twilio failed with error: {e1}")
        try:
            client = Client(TWILIO_SID2, TWILIO_AUTH2)
            print('Connected to secondary Twilio client')
            
            message = client.messages.create(
                from_=TWILIO_PHONE2,
                body=f"Secondary SMS account message:\n{msg}",
                to='+972584680232'
            )
            print('Sent SMS from secondary account')

        except Exception as e2:
            # If the second Twilio account also fails, log and pass
            print(f"Secondary Twilio failed with error: {e2}")
            pass  # Handle the failure or alert appropriately
            
    if 'message' in locals():
        print(f"SMS sent successfully with SID: {message.sid}")
    else:
        print("Both Twilio attempts failed, no SMS sent.")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
