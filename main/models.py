import flask
from flask import request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import Boolean
from db_conn import db, app
import json

class Serializer(object):
  __public__ = None

  def to_serializable_dict(self):
    dict = {}
    for public_key in self.__public__:
      value = getattr(self, public_key)
      if value:
        dict[public_key] = value
    return dict

class SWEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Serializer):
      return obj.to_serializable_dict()
    if isinstance(obj, (datetime)):
      return obj.isoformat()
    return json.JSONEncoder.default(self, obj)

def SWJsonify(*args, **kwargs):
  return app.response_class(json.dumps(dict(*args, **kwargs), cls=SWEncoder, 
         indent=None if request.is_xhr else 2), mimetype='application/json')
        # from https://github.com/mitsuhiko/flask/blob/master/flask/helpers.py

class Client(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(50))
    app_id = db.Column(db.Text())
    app_secret = db.Column(db.Text())
    passphrase = db.Column(db.Text())
    shortcode = db.Column(db.String(30))
    created_at = db.Column(db.String(50))

class AdminUser(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32))
    email = db.Column(db.String(60))
    password = db.Column(db.String(20))
    temp_pw = db.Column(db.String(20))
    name = db.Column(db.String(100))
    role = db.Column(db.String(30))
    active_sort = db.Column(db.String(30))
    added_by_id = db.Column(db.Integer)
    added_by_name = db.Column(db.String(100))
    join_date = db.Column(db.String(50))
    created_at = db.Column(db.String(50))

class Driver(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    plate_no = db.Column(db.String(10))
    name = db.Column(db.String(100))
    address = db.Column(db.Text())
    msisdn = db.Column(db.String(20))
    dl_no = db.Column(db.String(60))
    car_make = db.Column(db.String(60))
    car_model = db.Column(db.String(60))
    car_color = db.Column(db.String(60))
    status = db.Column(db.String(20))
    created_at = db.Column(db.String(50))

class Rider(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    facebook_id = db.Column(db.Text())
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    address = db.Column(db.Text())
    msisdn = db.Column(db.String(20))
    id_path = db.Column(db.Text())
    selfie_path = db.Column(db.Text())
    reg_status = db.Column(db.String(20))
    created_at = db.Column(db.String(50))

class Booking(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    rider_id = db.Column(db.Integer())
    rider_facebook_id = db.Column(db.Text())
    driver_id = db.Column(db.Integer())
    pickup = db.Column(db.Text())
    destination = db.Column(db.Text())
    km = db.Column(db.String(10))
    minutes = db.Column(db.String(10))
    fare = db.Column(db.Integer())
    date = db.Column(db.String(50))
    book_time = db.Column(db.String(50))
    driver_arrival_time = db.Column(db.String(50))
    dest_arrival_time = db.Column(db.String(50))
    booking_status = db.Column(db.String(30))
    created_at = db.Column(db.String(50))

class SVC(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer())
    facebook_id = db.Column(db.Text())
    token = db.Column(db.String(10))
    created_at = db.Column(db.String(50))