from flask import Flask
from flask_wtf.csrf import CsrfProtect
from celery import Celery

app = Flask(__name__)

app.config.from_object('app.config')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

CsrfProtect(app)

from app import views
