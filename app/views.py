from flask import render_template, flash, redirect, url_for, jsonify
from app import app, celery
from .forms import SuggestForm
from .tasks import start_context_aware_task, classify_images


@app.route('/')
@app.route('/index')
def index():
    form = SuggestForm()
    form.action = url_for('.suggest')
    form.keywords.value="test"
    return render_template('index.html', form=form)


@app.route('/suggest', methods=['POST'])
def suggest():
    form = SuggestForm()
    if form.validate_on_submit():
        keywords = (form.keywords.data).split()
        task_args = {'keywords': keywords}
        task = start_context_aware_task(
            classify_images,
            kwargs=task_args
        )
        status_url = url_for('.status', task_id=task.id)
        labels = app.config['CATEGORY_LABELS']
        return render_template('result.html', status_url=status_url, labels=labels, search_term=form.keywords.data)
    # form invalid
    return render_template('index.html', form=form)


@app.route('/status/<task_id>')
def status(task_id):
    task = classify_images.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state,
            'current': 0,
            'total': 1
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1)
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
