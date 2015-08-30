from app import app, celery
from flask import copy_current_request_context
from helper.dbpedia import fetch_uris_from_metadata
from fetch_commons import image_urls, images_and_metadata
from extraction import read_samples
from helper.dataset import Dataset
from feature.color import ColorFeature
from feature.histogram import HistogramFeature
from feature.blob import BlobFeature
from feature.gradient import GradientFeature
from feature.face import FaceFeature
from feature.brief import BriefFeature
from feature.geo import GeoFeature
from feature.format import FormatFeature
from feature.size import SizeFeature
from feature.words import WordsFeature
from feature.random import RandomFeature
import os


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
def classify_images(self, keywords=[]):
    if not len(keywords):
        raise AssertionError
    with app.app_context():
        update_progress(self, 10)
        # step 1 - query dpedia for related images based on given keywords
        uris = fetch_uris_from_metadata(keywords, 5)
        update_progress(self, 25)
        # step 2 - download images and metadata into temp folder with unique task id
        temp_folder = os.path.join(app.config['DOWNLOAD_DIRECTORY'], classify_images.request.id)
        dataset_file = os.path.join(temp_folder, 'dataset.json')
        images_and_metadata(uris, temp_folder, False)
        update_progress(self, 50)
        # step 3 - load dataset and extract features
        extractors = []
        extractors.append(SizeFeature())
        extractors.append(ColorFeature())
        extractors.append(HistogramFeature())
        extractors.append(GradientFeature())
        # todo this is not working yet, because dataset expects subdirectories for each category
        # solution: read individual samples and extract feature vectors
        dataset = Dataset(logging=True)
        dataset.read(temp_folder, extractors)
        dataset.save(dataset_file)
        update_progress(self, 75)
        # step 4 - use trained classifier to predict class
        # todo
        # step 5 - return list of url and prediced category pairs
        # todo
        # return the original, uncategorized image urls for now
        urls = image_urls(uris)
        result = {
            'current': 100,
            'total': 100,
            'result': urls
        }
        update_progress(self, 100)
        return result
