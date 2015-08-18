from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class SuggestForm(Form):
    keywords = StringField('keywords', validators=[DataRequired()])
