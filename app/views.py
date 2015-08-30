from flask import render_template, flash, redirect, url_for
from app import app
from .forms import SuggestForm
from helper.dbpedia import (fetch_uris_from_metadata, fetch_uris_from_articles,
    fetch_metadata)
from fetch_commons import image_urls

# todo specify query limit

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
        # todo run classification
        keywords = (form.keywords.data).split()
        uris = fetch_uris_from_metadata(keywords, 5)
        urls = image_urls(uris)
        print(uris)
    return render_template('result.html', uris=urls)
