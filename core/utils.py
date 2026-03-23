from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def sendmailForOtp(subject, template, to, context):

    print("Sending OTP To:",to)
    
    template_str = template + '.html' 

    html_message = render_to_string(template_str, {'data': context})
    plain_message = strip_tags(html_message)

    from_email = 'ravirathod100100@gmail.com'

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to],
        html_message=html_message,
    )