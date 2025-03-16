from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
import smtplib
import os



load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
PASSWORD = os.getenv("PASSWORD")


class EmailRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    subject: str
    msg: str

async def send_email(msg, title, src_email, src_password, dest_email):
    try:
        # Connect to SMTP server and send email
        connection = smtplib.SMTP("smtp.gmail.com", 587)
        print('first connection')
        connection.starttls()
        connection.login(user=src_email, password=src_password)
        print('loged in ')
        connection.sendmail(
            from_addr=src_email,
            to_addrs=dest_email, 
            msg=f"Subject: {title} \n\n{msg}"
        )
        print('sent mail')
        connection.close()
        
        
        return {"success": True}
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Authentication failed. Please check your email credentials."
        }
    except smtplib.SMTPRecipientsRefused:
        return {
            "success": False,
            "error": "Recipient address refused. Please check DEST_EMAILS."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }
