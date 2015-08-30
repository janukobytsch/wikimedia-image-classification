from app import app, celery
from flask import copy_current_request_context
from helper.dbpedia import fetch_uris_from_metadata
from fetch_commons import image_urls

# todo customize limit


def start_context_aware_task(func, kwargs={}):
    """
    Returns an async task decorated with a local copy of flask's request
    context. The decorater requires local scope with a request context on
    the stack.
    """
    @copy_current_request_context
    def create_context_aware_task(func, kwargs={}):
        """
        Factory method to wrap the task to be executed by the celery
        worker with the flask request context.
        """
        return func.apply_async(kwargs=kwargs)
    return create_context_aware_task(func, kwargs)


def update_progress(self, progress=0, total=100):
    self.update_state(
        state='PROGRESS',
        meta={'current': progress, 'total': total}
    )


@celery.task(bind=True)
def fetch_uris_by_keyword(self, keywords=[]):
    if not len(keywords):
        raise AssertionError
    with app.app_context():
        update_progress(self, 25)
        uris = fetch_uris_from_metadata(keywords, 5)
        update_progress(self, 50)
        urls = image_urls(uris)
        update_progress(self, 75)
        result = {
            'current': 100,
            'total': 100,
            'result': urls
        }
        return result


# @celery.task(bind=True)
# def random_task(self):
#     """Background task that runs a long function with progress reports."""
#     verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
#     adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
#     noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
#     message = ''
#     total = random.randint(10, 50)
#     for i in range(total):
#         if not message or random.random() < 0.25:
#             message = '{0} {1} {2}...'.format(random.choice(verb),
#                                               random.choice(adjective),
#                                               random.choice(noun))
#         self.update_state(state='PROGRESS',
#                           meta={'current': i, 'total': total,
#                                 'status': message})
#         time.sleep(1)
#     return {'current': 100, 'total': 100, 'status': 'Task completed!',
#             'result': 42}
