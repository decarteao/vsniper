
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    last_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    isBotOn = db.Column(db.Integer, default=0)

class Exchanges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True)

    api_key = db.Column(db.String(255), default='')
    api_secret = db.Column(db.String(255), default='')

class Monitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exchange1 = db.Column(db.String(100))
    exchange2 = db.Column(db.String(100))
    par = db.Column(db.String(100), default='')
    spread = db.Column(db.Float, default=0.01) # spread minimo

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


