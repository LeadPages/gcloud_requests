from setuptools import setup

from gcloud_requests import __version__

setup(
    name="gcloud_requests",
    description="Thread-safe client functionality for gcloud-python via requests.",
    long_description="""For documentation and usage examples, see the project on GitHub_.

    .. _GitHub: https://github.com/leadpages/gcloud_requests""",
    version=__version__,
    url="https://github.com/leadpages/gcloud_requests",
    author="Leadpages",
    author_email="opensource@leadpages.net",
    license="MIT",
    packages=["gcloud_requests"],
    install_requires=[
        "gcloud==0.12.1",
        "requests>=2.9.0,<3.0",
        "certifi==2015.09.06.2"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7"
    ]
)
