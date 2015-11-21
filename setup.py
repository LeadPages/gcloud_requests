from setuptools import setup

from gcloud_requests import __version__

setup(
    name='gcloud_requests',
    version=__version__,
    packages=['gcloud_requests'],
    install_requires=[
        'gcloud==0.7.0',
        'requests==2.7.0',
        'certifi'
    ]
)
