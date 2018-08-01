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

IPP_URL = 'https://devapi.globelabs.com.ph/smsmessaging/v1/outbound/%s/requests'

class BubbleAdmin(sqla.ModelView):
    column_display_pk = True

admin = Admin(app, name='bubble')
admin.add_view(BubbleAdmin(Client, db.session))
admin.add_view(BubbleAdmin(AdminUser, db.session))
admin.add_view(BubbleAdmin(Guardian, db.session))
admin.add_view(BubbleAdmin(GuardianStudent, db.session))

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
    # data = flask.request.args.to_dict()
    # verify_token = '1214'

    # if data['hub.verify_token'] == verify_token:
    #     return data['hub.challenge']

    data = request.json

    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']

    guardian = Guardian(
        client_no = 'lgmc2018',
        address_id = sender,
        medium = 'facebook'
        )
    db.session.add(guardian)
    db.session.commit()

    guardian_student = GuardianStudent(
        client_no = 'lgmc2018',
        guardian_id = guardian.id,
        student_no = message
        )

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