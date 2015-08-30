from flask import Flask
from flask_wtf.csrf import CsrfProtect
from celery import Celery

app = Flask(__name__)

app.config.from_object('app.config')
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

CsrfProtect(app)

from app import views
