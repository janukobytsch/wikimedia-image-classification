from flask import render_template, flash, redirect, url_for, jsonify
from app import app, celery
from .forms import SuggestForm
from helper.dbpedia import (fetch_uris_from_metadata, fetch_uris_from_articles,
    fetch_metadata)
from fetch_commons import image_urls
import random
import time

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
        # keywords = (form.keywords.data).split()
        # uris = fetch_uris_from_metadata(keywords, 5)
        # urls = image_urls(uris)
        # print(uris)
        task = long_task.apply_async()
        print('task id:', task.id)
    #return render_template('result.html', uris=urls)
    return render_template('result.html')


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
