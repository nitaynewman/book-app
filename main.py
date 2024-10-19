from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import smtplib
import uvicorn
from pydantic import BaseModel
from twilio.rest import Client

app = FastAPI()

TWILIO_PHONE = '+18584017119'
TWILIO_SID = 'AC59c49140f9d0e47bae9b21ce247753be'
TWILIO_AUTH = '80fed87f70a093fd8ba7fc9dafbb9f84'

MY_EMAIL = "nitaybusines@gmail.com"
PASSWORD = 'ghlx gdms ridi qbdz'

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
        connection.starttls()
        connection.login(user=MY_EMAIL, password=PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=[MY_EMAIL, email], 
            msg=f"Subject: {subject} to Nitay Newman\n\n{new_msg}"
        )
        connection.close()
        send_sms(new_msg)
        return {"success": True}
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False}
    
def send_sms(msg):
    client = Client(TWILIO_SID, TWILIO_AUTH)
    message = client.messages.create(
        from_='+18584017119',
        body=msg,
        to='+972584680232'
    )
    print(f"send sms {message.sid}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
