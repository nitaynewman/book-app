from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

TWILIO_PHONE1 = os.getenv('TWILIO_PHONE1')
TWILIO_SID1 = os.getenv('TWILIO_SID1')
TWILIO_AUTH1 = os.getenv('TWILIO_AUTH1')

TWILIO_PHONE2 = os.getenv('TWILIO_PHONE2')
TWILIO_SID2 = os.getenv('TWILIO_SID2')
TWILIO_AUTH2 = os.getenv('TWILIO_AUTH2')

TWILIO_PHONE3 = os.getenv('TWILIO_PHONE3')
TWILIO_SID3 = os.getenv('TWILIO_SID3')
TWILIO_AUTH3 = os.getenv('TWILIO_AUTH3')


def send_sms(msg, dest):
    credentials = [
        (TWILIO_SID1, TWILIO_AUTH1, TWILIO_PHONE1, "primary"),
        (TWILIO_SID2, TWILIO_AUTH2, TWILIO_PHONE2, "secondary"),
        (TWILIO_SID3, TWILIO_AUTH3, TWILIO_PHONE3, "tertiary")
    ]
    message = None
    
    for sid, auth, phone, account_name in credentials:
        try:
            client = Client(sid, auth)
            print(f'Connected to {account_name} Twilio client')
            
            message = client.messages.create(
                from_=phone,
                body=msg,
                to=dest
            )
            print(f'Sent SMS from {account_name} account')
            print(f"SMS sent successfully with SID: {message.sid}")
            break
            
        except Exception as e:
            print(f"{account_name.capitalize()} Twilio failed with error: {e}")
            continue
    
    if message is None:
        print("All Twilio attempts failed, no SMS sent.")


