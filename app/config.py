import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'CHANGE-ME'
DOWNLOAD_DIRECTORY = 'downloads'
CLASSIFIER_DIRECTORY = 'classifier'
WIKIMEDIA_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'classifier.pkl')
FACE_CLASSIFIER = os.path.join(CLASSIFIER_DIRECTORY, 'trained-faces.xml')
