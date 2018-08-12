from flask import url_for, request, session, redirect, jsonify, Response, make_response, current_app
from jinja2 import environment, FileSystemLoader
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import Boolean
from sqlalchemy import or_
from flask.ext import admin
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import Admin, BaseView, expose
from dateutil.parser import parse as parse_date
from flask import render_template, request
from flask import session, redirect
from datetime import timedelta
from datetime import datetime
from functools import wraps, update_wrapper
import threading
from threading import Timer
from multiprocessing.pool import ThreadPool
import calendar
from calendar import Calendar
from time import sleep
import requests
import datetime
from datetime import date
import time
import json
import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText as text
import os
import schedule
from werkzeug.utils import secure_filename
from tasks import send_notification
import db_conn
from db_conn import db, app
from models import *

ACCESS_TOKEN = 'EAAEOMP8YZAY0BAF3ao7EwxHNxzeGpf98NHE8jjkn64wNAMCsVhe5wfzcstjLZB3yTuyF4xL3FHvvx0WjRPjEp18T419IRP1H9YKlShuBQuANmMYXXb4nTeUDnllp0hq2tVPV1BXlwWpN1WoRfdKqhv6s0B5hYIOxt6Dxsyq0koqf5x2FGZC'
IPP_URL = 'https://devapi.globelabs.com.ph/smsmessaging/v1/outbound/%s/requests'
APP_ID = 'EGXMuB5eEgCMLTKxExieqkCGeGeGuBon'
APP_SECRET = 'f3e1ab30e23ea7a58105f058318785ae236378d1d9ebac58fe8b42e1e239e1c3'
PASSPHRASE = '24BUubukMQ'
SHORTCODE = '21588479'


class BubbleAdmin(sqla.ModelView):
    column_display_pk = True

admin = Admin(app, name='bubble')
admin.add_view(BubbleAdmin(Client, db.session))
admin.add_view(BubbleAdmin(AdminUser, db.session))
admin.add_view(BubbleAdmin(Driver, db.session))
admin.add_view(BubbleAdmin(Rider, db.session))
admin.add_view(BubbleAdmin(Booking, db.session))

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response    
    return update_wrapper(no_cache, view)

def facebook_reply(user_id, content):
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {'text': content}
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def facebook_quick_reply_msisdn(user_id, message):
    content = 'We will now process your request to receive notifications for student no: %s' % message
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {'text': content},
        "quick_replies":[
          {
            "content_type":"user_phone_number"
          }
        ]
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def send_svc(msisdn,token):
    content = 'Your Zundo verification code is: %s' % token
    message_options = {
        'app_id': APP_ID,
        'app_secret': APP_SECRET,
        'message': content,
        'address': msisdn,
        'passphrase': PASSPHRASE,
    }
    r = requests.post(IPP_URL%SHORTCODE,message_options)

def get_user_name(sender_id):
    args = {
        'fields': 'first_name,last_name',
        'access_token': ACCESS_TOKEN
    }
    r = requests.post("https://graph.facebook.com/%s"%sender_id,params=args)
    data = r.json()
    return '%s %s' % (data['first_name'], data['last_name'])


@app.route('/',methods=['GET','POST'])
@nocache
def index():
    return jsonify(
        status='success',
        message='working'
        ),200


@app.route('/facebook/webhook',methods=['GET','POST'])
@nocache
def messenger_webhook():
    if request.method == 'GET':
        data = flask.request.args.to_dict()
        verify_token = '1214'

        if data['hub.verify_token'] == verify_token:
            return data['hub.challenge']

    data = request.json

    sender_id = data['entry'][0]['messaging'][0]['sender']['id']

    # student = Student.query.filter_by(student_no=message).first()
    rider = Rider.query.filter_by(facebook_id=sender_id).first()
    if not rider or rider == None:
        rider = Rider(
            facebook_id=sender_id,
            reg_status='none',
            created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            )
        db.session.add(rider)
        db.session.commit()

    if 'postback' in data['entry'][0]['messaging'][0]:
        if data['entry'][0]['messaging'][0]['postback']['payload'] == 'GET_STARTED_PAYLOAD':
            rider.name = get_user_name(sender_id)
            db.session.commit()
            return jsonify(
                success = True
                ),200

        if data['entry'][0]['messaging'][0]['postback']['payload'] == 'book_payload':
            if rider.reg_status != 'done':
                rider.reg_status = 'name'
                db.session.commit()
                content = 'Hi, %s! Looks like it\'s you first time here. Let\'s get to know each other first, what\'s your mobile number?' % rider.name
                facebook_quick_reply_msisdn(sender_id,content)
            return jsonify(
                success = True
                ),200

    # if rider.reg_status == 'name':
    #     message = data['entry'][0]['messaging'][0]['message']['text']
    #     rider.name = message
    #     rider.reg_status = 'msisdn'
    #     db.session.commit()
    #     content = 'What\'s your mobile number?'
    #     facebook_reply(sender_id,content)
    #     return jsonify(
    #         success = True
    #         ),200

    if rider.reg_status == 'msisdn':
        msisdn = data['entry'][0]['messaging'][0]['postback']['payload']
        rider.msisdn = msisdn
        rider.reg_status = 'svc'
        db.session.commit()
        svc = SVC(
            user_id = rider.id,
            facebook_id = rider.facebook_id,
            token = str(uuid.uuid4().fields[-1])[:6],
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            )
        db.session.add(svc)
        db.session.commit()
        send_svc(rider.msisdn,svc.token)
        content = 'We sent a one time verification code to your mobile number. Please send the code back to us now.'
        facebook_reply(sender_id,content)
        return jsonify(
            success = True
            ),200

    if rider.reg_status == 'svc':
        message = data['entry'][0]['messaging'][0]['message']['text']
        svc = SVC.query.filter_by(user_id=rider.id, token=message).first()
        if not svc or svc == None:
            content = 'Invalid verification code. Please try again.'
            facebook_reply(sender_id,content)
            return jsonify(
                success = True
                ),200
        svc.status = 'Done'
        rider.reg_status = 'id_pic'
        db.session.commit()
        content = 'Phone verification successful! You\'re almost there. We just need a picture of 1 valid ID for the safety of our drivers. :)'
        facebook_reply(sender_id,content)
        return jsonify(
            success = True
            ),200

    if rider.reg_status == 'id_pic':
        image = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['url']
        rider.id_path = image
        rider.reg_status = 'selfie'
        db.session.commit()
        content = 'Last step! Please send a selfie of you holding the valid ID you just sent us.'
        facebook_reply(sender_id,content)
        return jsonify(
            success = True
            ),200

    if rider.reg_status == 'selfie':
        image = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['url']
        rider.selfie_path = image
        rider.reg_status = 'done'
        db.session.commit()
        content = 'Okay, we\'re good to go! Where do you want to be picked up?'
        facebook_quick_reply()
        return jsonify(
            success = True
            ),200


@app.route('/db/rebuild',methods=['GET','POST'])
def rebuild_database():
    db.drop_all()
    db.create_all()

    return jsonify(
        status = 'success',
        message = 'Database successfully rebuilt'
        ),201


if __name__ == '__main__':
    app.run(port=8000,debug=True,host='0.0.0.0')