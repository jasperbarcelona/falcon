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
MAPQUEST_API_KEY = 'tYvwHGIn327Vjzkk7e7spoSxImgvrGvz'
MAPQUEST_URL = 'http://open.mapquestapi.com/directions/v2/routematrix'


class BubbleAdmin(sqla.ModelView):
    column_display_pk = True

admin = Admin(app, name='bubble')
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
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {
        'text': message,
        "quick_replies":[
          {
            "content_type":"user_phone_number"
          }
        ]
        },
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def facebook_quick_reply_pickup(user_id, message):
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {
        'text': message,
        "quick_replies":[
          {
            "content_type":"location"
          }
        ]
        },
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def facebook_quick_reply_destination(user_id, message):
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {
        'text': message,
        "quick_replies":[
          {
            "content_type":"location"
          },
          {
            "content_type":"text",
            "title":'Change Pickup Location',
            "payload":'change_pickup'
            }
        ]
        },
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def facebook_quick_reply_fare(user_id, message):
    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {
        'text': message,
        "quick_replies":[
            {
            "content_type":"text",
            "title":'Book',
            "payload":'proceed_with_booking'
            },
            {
            "content_type":"text",
            "title":'Cancel',
            "payload":'cancel_booking'
            }
        ]
        },
    }
    resp = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN, json=data)

def generate_clone_svc():
    unique = False
    while unique == False:
        new_token = str(uuid.uuid4().fields[-1])[:6]
        existing = SVC.query.filter_by(token=new_token).first()
        if not existing or existing == None:
            unique = True
    return new_token


def facebook_quick_reply_svc(user_id, message):
    # tokens = []
    # real_token = SVC.query.filter_by(facebook_id=user_id).first().token
    # tokens.append(generate_clone_svc())
    # tokens.append(generate_clone_svc())
    # tokens.append(real_token)

    # choice_1 = random.choice(tokens)
    # tokens.remove(choice_1)
    # choice_2 = random.choice(tokens)
    # tokens.remove(choice_2)
    # choice_3 = random.choice(tokens)
    # tokens.remove(choice_3)

    data = {
        "messaging_type": 'RESPONSE',
        "recipient": {'id': user_id},
        "message": {
        'text': message,
        "quick_replies":[
            {
            "content_type":"text",
            "title":'Change Mobile Number',
            "payload":'change_msisdn'
            }
        ]
        },
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
    params = dict(
        fields='first_name,last_name',
        access_token=ACCESS_TOKEN
    )

    r = requests.get("https://graph.facebook.com/%s"%sender_id,params=params)
    data = r.json()
    return data

def register(rider, data):
    sender_id = data['entry'][0]['messaging'][0]['sender']['id']
    if rider.reg_status == 'msisdn':
        if 'message' not in data['entry'][0]['messaging'][0]:
            content = 'Let\'s finish up with your registration first. What\'s your mobile number?'
            facebook_quick_reply_msisdn(sender_id,content)
            return jsonify(
            success = True
            ),200
        if 'quick_reply' in data['entry'][0]['messaging'][0]['message']:
            msisdn = data['entry'][0]['messaging'][0]['message']['quick_reply']['payload']
        else:
            msisdn = data['entry'][0]['messaging'][0]['message']['text']
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
        content = 'We sent a one time verification code to your mobile number. Please enter the code below and click send.'
        facebook_quick_reply_svc(sender_id,content)
        return jsonify(
            success = True
            ),200

    if rider.reg_status == 'svc':
        if 'message' not in data['entry'][0]['messaging'][0]:
            content = 'Let\'s finish up with your registration first. Please enter the verification code we sent to your mobile number.'
            facebook_reply(sender_id,content)
            return jsonify(
            success = True
            ),200
        if 'quick_reply' in data['entry'][0]['messaging'][0]['message']:
            rider.reg_status = 'msisdn'
            db.session.commit()
            content = 'What\'s your mobile number?'
            facebook_quick_reply_msisdn(sender_id,content)
            return jsonify(
                success = True
                ),200
        svc = data['entry'][0]['messaging'][0]['message']['text']
        svc = SVC.query.filter_by(user_id=rider.id, token=svc).first()
        if not svc or svc == None:
            content = 'Invalid verification code. Please try again.'
            facebook_quick_reply_svc(sender_id,content)
            return jsonify(
                success = True
                ),200
        db.session.delete(svc)
        rider.reg_status = 'id_pic'
        db.session.commit()
        content = 'Phone verification successful! You\'re almost there, we just need a picture of one (1) valid ID/school ID for the safety of our drivers.'
        facebook_reply(sender_id,content)
        return jsonify(
            success = True
            ),200

    if rider.reg_status == 'id_pic':
        if 'message' not in data['entry'][0]['messaging'][0]:
            content = 'Let\'s finish up with your registration first. Please send a photo of your valid ID/school ID.'
            facebook_reply(sender_id,content)
            return jsonify(
            success = True
            ),200
        if 'attachments' not in data['entry'][0]['messaging'][0]['message']:
            content = 'Please send a photo of your valid ID/school ID.'
            facebook_reply(sender_id,content)
            return jsonify(
                success = True
                ),200
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
        if 'message' not in data['entry'][0]['messaging'][0]:
            content = 'Let\'s finish up with your registration first. Please send a selfie of you holding your valid ID/school ID.'
            facebook_reply(sender_id,content)
            return jsonify(
            success = True
            ),200
        if 'attachments' not in data['entry'][0]['messaging'][0]['message']:
            content = 'Please send a photo of you holding your valid ID/school ID.'
            facebook_reply(sender_id,content)
            return jsonify(
                success = True
                ),200
        image = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['url']
        rider.selfie_path = image
        rider.reg_status = 'done'
        db.session.commit()
        content = 'Okay, we\'re good to go! Just tap "Book a Ride" below.'
        facebook_reply(sender_id, content)
        return jsonify(
            success = True
            ),200

def calculate_fare(booking):
    params = dict(
        key=MAPQUEST_API_KEY
    )

    data = {
        'locations': [
        '%s,%s' % (booking.pickup_lat, booking.pickup_long),
        '%s,%s' % (booking.destination_lat, booking.destination_long)
        ]
    }

    r = requests.post(MAPQUEST_URL,params=params,json=data)
    data = r.json()
    miles = data['distance'][1]
    secs = data['time'][1]
    minutes = secs/60
    km = float(miles) * 1.60934
    fare = (km*14)+(minutes*2)+40   

    content = 'Your fair is PHP %s. Would you like to continue?' % '{0:.2f}'.format(round(fare))
    facebook_quick_reply_fare(booking.rider_facebook_id,content)

    return jsonify(
        success = True
        ),200


@app.route('/',methods=['GET','POST'])
@nocache
def index():
    if not session:
        return redirect('/login')
    user = AdminUser.query.filter_by(id=session['user_id']).first()
    rider_count = Rider.query.count()
    driver_count = Driver.query.count()
    booking_count = Booking.query.count()
    day_booking_count = Booking.query.filter_by(date=datetime.datetime.now().strftime('%B %d, %Y')).count()
    return flask.render_template(
        'index.html',
        rider_count=rider_count,
        driver_count=driver_count,
        booking_count=booking_count,
        day_booking_count=day_booking_count,
        user=user
        )


@app.route('/login',methods=['GET','POST'])
@nocache
def login_page():
    if session:
        return redirect('/')
    return flask.render_template('login.html')


@app.route('/user/authenticate',methods=['GET','POST'])
def authenticate_user():
    data = flask.request.form.to_dict()
    user = AdminUser.query.filter_by(email=data['user_email'],password=data['user_password']).first()
    if not user or user == None:
        return jsonify(status='failed', error='Invalid email or password.')
    session['user_name'] = user.name
    session['user_id'] = user.id
    return jsonify(status='success', error=''),200


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
            if rider.reg_status == 'none':
                user_info = get_user_name(sender_id)
                rider.first_name = user_info['first_name']
                rider.last_name = user_info['last_name']
                rider.reg_status = 'msisdn'
                content = 'Hi, %s! Looks like it\'s your first time here. Let\'s get to know each other first, what\'s your mobile number?' % rider.first_name
                facebook_quick_reply_msisdn(sender_id,content)
                db.session.commit()
                return jsonify(
                    success = True
                    ),200

            if rider.reg_status != 'done':
                return register(rider, data)

            content = 'Welcome back, %s! We missed you. Just tap "Book a Ride" below to start.' % rider.first_name
            facebook_reply(sender_id,content)
            return jsonify(
                success = True
                ),200

        if data['entry'][0]['messaging'][0]['postback']['payload'] == 'book_payload':
            if rider.reg_status != 'done':
                if rider.reg_status == 'none':
                    rider.reg_status = 'msisdn'
                    db.session.commit()
                return register(rider, data)
            unfinished_booking = Booking.query.filter(Booking.rider_id==rider.id, Booking.booking_status!='done').first()
            if unfinished_booking or unfinished_booking != None:
                db.session.delete(unfinished_booking)
                db.session.commit()
            new_booking = Booking(
                rider_id=rider.id,
                rider_facebook_id=sender_id,
                date=datetime.datetime.now().strftime('%B %d, %Y'),
                booking_status='pickup_data',
                created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
                )
            db.session.add(new_booking)
            db.session.commit()
            content = 'Where do you want to be picked up?'
            facebook_quick_reply_pickup(sender_id,content)
            return jsonify(
                success = True
                ),200

    if rider.reg_status == 'done':
        booking = Booking.query.filter(Booking.rider_id==rider.id, Booking.booking_status!='done').first()
        if not booking or booking == None:
            content = 'To start looking for drivers, please click "Book a Ride" below.'
            facebook_reply(sender_id,content)
            return jsonify(
                success = True
                ),200
        if 'attachments' not in data['entry'][0]['messaging'][0]['message']:
            if booking.booking_status == 'pickup_data':
                content = 'Please pin your pickup location.'
                facebook_quick_reply_pickup(sender_id,content)
            elif booking.booking_status == 'destination_data':
                if 'quick_reply' in data['entry'][0]['messaging'][0]['message']:
                    booking.booking_status = 'pickup_data'
                    db.session.commit()
                    content = 'Where do you want to be picked up?'
                    facebook_quick_reply_pickup(sender_id,content)
                    return jsonify(
                        success = True
                        ),200
                content = 'Please pin your destination.'
                facebook_quick_reply_destination(sender_id,content)
            return jsonify(
                success = True
                ),200
        if data['entry'][0]['messaging'][0]['message']['attachments'][0]['type'] != 'location':
            if booking.booking_status == 'pickup_data':
                content = 'Please pin your pickup location.'
                facebook_quick_reply_pickup(sender_id,content)
            elif booking.booking_status == 'destination_data':
                if 'quick_reply' in data['entry'][0]['messaging'][0]['message']:
                    booking.booking_status = 'pickup_data'
                    db.session.commit()
                    content = 'Where do you want to be picked up?'
                    facebook_quick_reply_pickup(sender_id,content)
                    return jsonify(
                        success = True
                        ),200
                content = 'Please pin your destination.'
                facebook_quick_reply_destination(sender_id,content)
            return jsonify(
                success = True
                ),200
        if booking.booking_status == 'pickup_data':
            booking.pickup_lat = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['coordinates']['lat']
            booking.pickup_long = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['coordinates']['long']
            booking.booking_status = 'destination_data'
            db.session.commit()
            content = 'Where do you want to go?'
            facebook_quick_reply_destination(sender_id,content)
            return jsonify(
                success = True
                ),200
        elif booking.booking_status == 'destination_data':
            booking.destination_lat = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['coordinates']['lat']
            booking.destination_long = data['entry'][0]['messaging'][0]['message']['attachments'][0]['payload']['coordinates']['long']
            booking.booking_status = 'calculate'
            db.session.commit()
            
            # content = 'Calculating fare...'
            # facebook_reply(sender_id,content)
            return calculate_fare(booking)

    return register(rider, data)



@app.route('/db/rebuild',methods=['GET','POST'])
def rebuild_database():
    db.drop_all()
    db.create_all()

    admin = AdminUser(
        email='jasper@pisara.tech',
        password='password123',
        temp_pw='password1234',
        name='Jasper Barcelona',
        role='Administrator',
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        )

    db.session.add(admin)
    db.session.commit()

    return jsonify(
        status = 'success',
        message = 'Database successfully rebuilt'
        ),201


if __name__ == '__main__':
    app.run(port=8000,debug=True,host='0.0.0.0')