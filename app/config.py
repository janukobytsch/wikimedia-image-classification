import os

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

SECRET_KEY = 'CHANGE-ME'
WTF_CSRF_ENABLED = True

DOWNLOAD_DIRECTORY = 'downloads'
CLASSIFIER_DIRECTORY = 'classifier'

WIKIMEDIA_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'classifier.pkl')
FACE_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'trained-faces.xml')
DATASET_CONFIG = os.path.join(CLASSIFIER_DIRECTORY, 'dataset.json')
WORDS_CONFIG = os.path.join(CLASSIFIER_DIRECTORY, 'words.json')

CATEGORY_LABELS = ['sign', 'chart', 'architecture', 'drawn', 'painting', 'social', 'portrait', 'screenshot', 'flag', 'vehicles', 'logo', 'document', 'object', 'scheme', 'map', 'icon', 'landscape', 'scenery']
