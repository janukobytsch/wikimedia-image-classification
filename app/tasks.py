import os
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
def classify_images(self, keywords=[]):
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
            # todo word extractor
            return extractors

        # keep track of progress
        progress_observer = ProgressObserver(self)
        progress_observer.update(5)

        # query dpedia for related images based on given keywords
        uris = fetch_uris_from_metadata(keywords, 20)
        progress_observer.update(20)

        # download images and metadata into temp folder with unique task id
        temp_folder = os.path.join(app.config['DOWNLOAD_DIRECTORY'], classify_images.request.id)
        images_and_metadata(uris, temp_folder, False, observer=progress_observer)
        progress_observer.update(80)

        # load dataset and extract features
        dataset = Dataset(logging=True)
        dataset.read(root=temp_folder, extractors=supported_extractors(), unlabeled_data=True)
        # todo load stds and means from file in trained classifier folder
        dataset.means = [1695.732868757259, 1414.950445218738, 1.384887907330568, 216.1749903213318, 154.80214540772505, 152.15413202447488, 143.7004137936062, 4150.685842181552, 3937.3446884489376, 4449.475437883657, 0.5123575515540312, 0.14720864467643002, 0.04413522328233885, 0.03347732242668409, 0.16494395351668362, 0.0494684388459398, 0.015449455990793167, 0.032959409707099305, 0.4419384349744725, 0.11652856605993515, 0.08996383542936992, 0.07180846388193235, 0.06754363529265874, 0.05015303448932927, 0.04208469723159843, 0.11997933264070364, 0.09824358637001548, 0.06667943135555797, 0.07210175399396293, 0.0796639696830841, 0.08120490061973723, 0.0826007696809669, 0.09522535890467722, 0.42428022939199816, 0.26483491835242207, 0.05752596560627065, 0.07173912280101066, 0.11721218362167335, 0.26913874337965943, 0.05590539222528574, 0.06582986788727582, 0.09781380612639899, 0.2237708091366628, 0.08672086720867209, 0.6875725900116144, 0.0027100271002710027, 0.1889276035617499, 0.024003097173828883, 0.09678668215253582]
        dataset.stds = [1508.3798051990311, 1218.6850557312644, 0.9934899053060378, 964.7906608795093, 56.75993914928039, 56.66462743398411, 60.23508593548298, 3039.0849228676466, 2797.344846729791, 3226.5404013122675, 0.33981398608633767, 0.19288973991085745, 0.08977905913397112, 0.0873596513692464, 0.22022137627377106, 0.10207134982328261, 0.04602464415295545, 0.08572294414925119, 0.339845849093632, 0.13946761583019757, 0.11216800604024997, 0.08778998273207686, 0.09050809725557746, 0.07001909972917415, 0.0687263483026039, 0.18335703682486287, 0.14401694501952175, 0.08057513330414341, 0.07940674522371036, 0.08962784972825799, 0.0919917662143114, 0.09418301689730946, 0.10622055201200861, 0.29877303667299243, 0.17091504382402684, 0.04345801341725326, 0.05398831560615165, 0.09462669069236958, 0.15628135458447823, 0.0442493644099026, 0.0523613344142618, 0.08024458529849858, 0.6885661155738411, 0.2814255823468179, 0.46348303472330804, 0.051987333586046756, 0.39145110061688193, 0.1530586439894602, 0.29566707681181315]
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
            entry = {
                'thumbnail': sample.thumbnail,
                'image': sample.url,
                'label': label,
                'title': sample.url
            }
            suggestions.append(entry)
        result = {
            'current': 100,
            'total': 100,
            'result': suggestions
        }

        # cleanup temporary directory
        delete_directory(temp_folder)

        progress_observer.update(100)

        return result
