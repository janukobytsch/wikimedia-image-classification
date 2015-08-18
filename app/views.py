from flask import render_template, flash, redirect, url_for
from app import app
from .forms import SuggestForm


@app.route('/')
@app.route('/index')
def index():
    form = SuggestForm()
    form.action = url_for('.suggest')
    return render_template('index.html', form=form)


@app.route('/suggest', methods=['POST'])
def suggest():
    form = SuggestForm()
    if form.validate_on_submit():
        # todo run keyword queries + classification
        pass
    else:
        # todo show error
        pass
