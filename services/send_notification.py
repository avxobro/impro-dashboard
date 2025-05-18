import os
import json
from twilio.rest import Client

class WhatsAppSender:
    def __init__(self, twilio_sid: str, twilio_token: str, whatsapp_number: str):
        '''
        Initializes WhatsAppSender with Twilio credentials and target WhatsApp number.

        Args:
            twilio_sid (str): Twilio Account SID.
            twilio_token (str): Twilio Auth Token.
            whatsapp_number (str): Target WhatsApp number in E.164 format.
        '''
        self.client = Client(twilio_sid, twilio_token)
        self.whatsapp_number = whatsapp_number

    def send_message(self, content: str) -> bool:

        try:
            message = self.client.messages.create(
                from_='whatsapp:+14155238886',
                to=f'whatsapp:{self.whatsapp_number}',
                body=content
            )
            print("message sent successfully")
            return True
        except Exception as e:
            print(f"❌ WhatsApp send error: {e}")
            return False
