from flask import Flask
from flask_wtf.csrf import CsrfProtect

app = Flask(__name__)
app.config.from_object('app.config')
CsrfProtect(app)

from app import views
