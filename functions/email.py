from dotenv import load_dotenv
import smtplib
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
MY_EMAIL = os.getenv('MY_EMAIL')
PASSWORD = os.getenv('PASSWORD')
SS_EMAIL = os.getenv('SS_EMAIL')
SS_PASSWORD = os.getenv('SS_PASSWORD')


def send_email(src_email, dest_email, title, message):
    """Synchronous email sending function"""
    try:
        logger.info(f"Starting email send process to {dest_email}")
        
        if src_email == 'smartsen':
            src_email = SS_EMAIL
            password = SS_PASSWORD
        else:
            src_email = MY_EMAIL
            password = PASSWORD
        
        logger.info(f"Using email: {src_email}")
        
        try:
            logger.info("Attempting connection with SSL on port 465")
            connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
            connection.login(user=src_email, password=password)
            logger.info("Successfully logged in with SSL")
        except Exception as e:
            logger.warning(f"SSL connection failed: {e}, trying STARTTLS on port 587")
            connection = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
            connection.starttls()
            connection.login(user=src_email, password=password)
            logger.info("Successfully logged in with STARTTLS")
        
        connection.sendmail(
            from_addr=src_email,
            to_addrs=dest_email, 
            msg=f"Subject: {title}\n\n{message}".encode('utf-8')
        )
        logger.info("Email sent successfully")
        connection.quit()
        
        return {"success": True}
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return {
            "success": False,
            "error": "Authentication failed. Please check your email credentials."
        }
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e}")
        return {
            "success": False,
            "error": "Recipient address refused. Please check DEST_EMAILS."
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }
    
