import os
import json
import numpy as np
from app import app, celery
from flask import copy_current_request_context
from helper.dbpedia import fetch_uris_from_metadata
from helper.download import delete_directory
from fetch_commons import images_and_metadata
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
from sklearn.externals import joblib


class Observer:
    def update(observable, arg):
        pass


class ProgressObserver(Observer):
    def __init__(self, outer, current=0, total=100):
        self.outer = outer
        self.current = current
        self.total = total
    def update(self, current=0, total=100, offset=0):
        self.current = offset + (current / total * 100)
        self.outer.update_state(
            state='PROGRESS',
            meta={'current': self.current, 'total': self.total}
        )


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


@celery.task(bind=True)
def classify_images(self, keywords=[], limit=25):
    """
    Worker task to retrieve a list of automatically categorized images from
    Wikimedia Commons from a given list of keywords.
    """
    if not len(keywords):
        raise AssertionError

    with app.app_context():
        def supported_extractors():
            extractors = []
            extractors.append(SizeFeature())
            extractors.append(ColorFeature())
            extractors.append(HistogramFeature())
            extractors.append(GradientFeature())
            extractors.append(FaceFeature(app.config['FACE_CLASSIFIER']))
            extractors.append(GeoFeature())
            extractors.append(FormatFeature())
            extractors.append(WordsFeature.create_from(app.config['WORDS_CONFIG']))
            return extractors

        def create_response_entry(label, sample):
            return {
                'thumbnail': sample.thumbnail,
                'image': sample.url,
                'label': label,
                'title': sample.url
            }

        def create_response(entries):
            return {
                'current': 100,
                'total': 100,
                'result': entries
            }

        # keep track of progress
        progress_observer = ProgressObserver(self)
        progress_observer.update(5)

        # query dpedia for related images based on given keywords
        if limit > app.config['QUERY_LIMIT']:
            limit = app.config['QUERY_LIMIT']
        searchterm = ' '.join(keywords)
        uris = fetch_uris_from_metadata(searchterm, limit, multiple=False)
        progress_observer.update(20)

        # download images and metadata into temp folder with unique task id
        temp_folder = os.path.join(app.config['DOWNLOAD_DIRECTORY'], classify_images.request.id)
        images_and_metadata(uris, temp_folder, False, observer=progress_observer)
        progress_observer.update(80)

        # load dataset and extract features
        dataset = Dataset(logging=True)
        dataset.read(root=temp_folder, extractors=supported_extractors(), unlabeled_data=True)
        dataset_config = json.load(open(app.config['DATASET_CONFIG']))
        dataset.means = dataset_config['means']
        dataset.stds = dataset_config['stds']
        dataset.normalize()
        progress_observer.update(90)

        # predict labels using the trained classifier
        classifier = joblib.load(app.config['WIKIMEDIA_CLASSIFIER'])
        predictions = classifier.predict(dataset.data)
        progress_observer.update(95)

        # build response
        suggestions = []
        for index, sample in enumerate(dataset.samples):
            label = np.asscalar(predictions[index])
            entry = create_response_entry(label, sample)
            suggestions.append(entry)
        result = create_response(suggestions)

        # cleanup temporary directory
        delete_directory(temp_folder)

        progress_observer.update(100)

        return result
