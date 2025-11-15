import requests
import logging
from datetime import datetime

# It's recommended to move sensitive data like API keys to environment variables or settings
# TODO: Move Authorization to Django settings or environment variables
SMS_API_AUTHORIZATION = "Basic YXRoaW06TWFtYXNob2tv"
SMS_API_URL = 'https://messaging-service.co.tz/api/sms/v1/text/single'
SMS_SENDER = "sotech"

logger = logging.getLogger(__name__)

def generate_reference():
    """Generate a unique reference for SMS tracking."""
    return f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def send_otp_via_sms(phoneNumber, otp):
    try:
        # Format phone number - ensure it has country code
        if not phoneNumber.startswith('+'):
            phoneNumber = '+' + phoneNumber

        headers = {
            'Authorization': SMS_API_AUTHORIZATION,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        reference = generate_reference()  # Generate the reference

        # Improve message format for clarity
        payload = {
            "from": SMS_SENDER,
            "to": phoneNumber,
            "text": f"Your verification code is: {otp}. Do not share this code with anyone.",
            "reference": reference,
        }

        # Enhanced logging
        logger.info(f"Sending OTP to: {phoneNumber}, Reference: {reference}")

        response = requests.post(SMS_API_URL, headers=headers, json=payload)
        response_data = response.json() if response.text else {}

        if response.status_code == 200:
            logger.info(f"OTP message sent successfully! Response: {response_data}")
            return True
        else:
            logger.error(f"Failed to send OTP message. Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.exception(f'Error sending OTP: {e}')
        return False

def send_sms(phone_number, message):
    """General purpose function to send a text message."""
    try:
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        headers = {
            'Authorization': SMS_API_AUTHORIZATION,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        reference = generate_reference()

        payload = {
            "from": SMS_SENDER,
            "to": phone_number,
            "text": message,
            "reference": reference,
        }

        logger.info(f"Sending SMS to: {phone_number}, Reference: {reference}")
        response = requests.post(SMS_API_URL, headers=headers, json=payload)
        response_data = response.json() if response.text else {}

        if response.status_code == 200:
            logger.info(f"Message sent successfully! Response: {response_data}")
            return True
        else:
            logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.exception(f'Error sending SMS: {e}')
        return False
