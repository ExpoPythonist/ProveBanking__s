from twilio.rest import TwilioRestClient
from django.conf import settings


def send_sms(to, body):
    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    message = client.messages.create(from_=settings.TWILIO_NUMBER, to=to, body=body)


def buy_masked_phone():
    return None
    '''
    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    numbers = client.phone_numbers.search(country="US", type="local", sms_enabled=True, voice_enabled=True)

    if numbers:
        number = numbers[0].purchase(
            sms_application_sid=settings.TWILIO_APP_SID,
            voice_application_sid=settings.TWILIO_APP_SID,
        ).phone_number
        return number
    '''
