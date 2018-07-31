from celery import Celery
import db_conn
from db_conn import db
from models import *
import requests
import uuid
from cStringIO import StringIO
from dateutil.parser import parse as parse_date
import datetime
import time
from time import sleep
from flask import jsonify
import random
import string
import xlrd
import pdfkit

app = Celery('tasks', broker='amqp://admin:password@rabbitmq/falcon')

IPP_URL = 'https://devapi.globelabs.com.ph/smsmessaging/v1/outbound/%s/requests'

@app.task
def send_notification(client_no,status,waybill_no,msisdn):
    client = Client.query.filter_by(client_no=client_no).first()

    notification = Notification(
        client_no=client_no,
        waybill_no=waybill_no,
        notification_type=status,
        msisdn=msisdn
        )
    db.session.add(notification)
    db.session.commit()

    if status == 'Pending':
        message = 'We have received your package. We will notify you once it has been shipped. Your waybill number is %s.' % waybill_no

    elif status == 'Done':
        waybill = Package.query.filter_by(waybill_no=waybill_no).first()
        if waybill.pickup_type == 'Pick Up':
            pickup_action = 'picked up by'
        else:
            pickup_action = 'delivered to'
 
        message = 'Your package with waybill number %s has been %s %s on %s at %s. Thank you.' % (waybill_no, pickup_action, waybill.pickup_name, waybill.pickup_date, waybill.pickup_time)

    message_options = {
        'app_id': client.app_id,
        'app_secret': client.app_secret,
        'message': message,
        'address': notification.msisdn,
        'passphrase': client.passphrase,
    }

    try:
        r = requests.post(IPP_URL%client.shortcode,message_options)           
        if r.status_code == 201:
            notification.status = 'Success'
            notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        else:
            notification.status = 'Failed'
            notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')

        db.session.commit()

    except requests.exceptions.ConnectionError as e:
        notification.status = 'Failed'
        notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        db.session.commit()

    return

@app.task
def send_arrival_notifications(client_no,batch_id):
    client = Client.query.filter_by(client_no=client_no).first()
    batch = ArrivalBatch.query.filter_by(id=batch_id).first()
    notifications = ArrivalNotification.query.filter_by(batch_id=batch_id).all()

    for notification in notifications:
        message = 'We are glad to let you know that your package with waybill number %s has arrived at our warehouse. We will notify you once it has been delivered or picked up.' % notification.waybill_no
        recipient_message_options = {
        'app_id': client.app_id,
        'app_secret': client.app_secret,
        'message': message,
        'address': notification.recipient_msisdn,
        'passphrase': client.passphrase,
        }

        sender_message_options = {
        'app_id': client.app_id,
        'app_secret': client.app_secret,
        'message': message,
        'address': notification.sender_msisdn,
        'passphrase': client.passphrase,
        }

        try:
            r = requests.post(IPP_URL%client.shortcode,recipient_message_options)           
            if r.status_code == 201:
                notification.recipient_notification_status = 'Success'
                notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            else:
                notification.recipient_notification_status = 'Failed'
                notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')

            db.session.commit()

        except requests.exceptions.ConnectionError as e:
            notification.recipient_notification_status = 'Failed'
            notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            db.session.commit()

        try:
            n = requests.post(IPP_URL%client.shortcode,sender_message_options)           
            if n.status_code == 201:
                notification.sender_notification_status = 'Success'
                notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            else:
                notification.sender_notification_status = 'Failed'
                notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')

            db.session.commit()

        except requests.exceptions.ConnectionError as e:
            notification.sender_notification_status = 'Failed'
            notification.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            db.session.commit()

        notification.overall_status = 'Done'
        db.session.commit()
        batch.done = ArrivalNotification.query.filter_by(batch_id=batch.id,overall_status='Done').count()
        batch.pending = ArrivalNotification.query.filter_by(batch_id=batch.id,overall_status='Pending').count()
        db.session.commit()

    batch.done = ArrivalNotification.query.filter_by(batch_id=batch.id).count()
    batch.pending = 0
    db.session.commit()

    return

@app.task
def create_pdf(report_id,pdf_data):
    report = Report.query.filter_by(id=report_id).first()
    try:
        pdfkit.from_string(pdf_data, 'static/reports/%s.pdf'%report.name)
        report.status = 'Success'
        db.session.commit()
        return

    except requests.exceptions.ConnectionError as e:
        report.status = 'Failed'
        db.session.commit()
        return