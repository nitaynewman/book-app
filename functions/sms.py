
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

# Access the environment variables
TWILIO_PHONE = os.getenv('TWILIO_PHONE')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH = os.getenv('TWILIO_AUTH')

TWILIO_PHONE2 = os.getenv('TWILIO_PHONE2')
TWILIO_SID2 = os.getenv('TWILIO_SID2')
TWILIO_AUTH2 = os.getenv('TWILIO_AUTH2')


def send_sms(msg):
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
            print(f"Secondary Twilio failed with error: {e2}")
            pass
            
    if 'message' in locals():
        print(f"SMS sent successfully with SID: {message.sid}")
    else:
        print("Both Twilio attempts failed, no SMS sent.")

