from celery import Celery
from django.core.mail import send_mail


import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()

app=Celery('celery_task.tasks',broker='redis://192.168.12.186:6379/3')


@app.task
def send_email_task(subject, message, sender, receiver, html_message):
    print('celery...begin')
    send_mail(subject, message, sender, receiver, html_message=html_message)
    print('celery...end')