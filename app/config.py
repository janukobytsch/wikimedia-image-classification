import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'CHANGE-ME'
DOWNLOAD_DIRECTORY = 'downloads'
CLASSIFIER_DIRECTORY = 'classifier'
WIKIMEDIA_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'classifier.pkl')
FACE_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'trained-faces.xml')
CATEGORY_LABELS = ['sign', 'chart', 'architecture', 'drawn', 'painting', 'social', 'portrait', 'screenshot', 'flag', 'vehicles', 'logo', 'document', 'object', 'scheme', 'map', 'icon', 'landscape', 'scenery']
