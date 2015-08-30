from flask.ext.wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired, Required


class SuggestForm(Form):
    keywords = StringField('keywords', validators=[Required(), DataRequired()])
