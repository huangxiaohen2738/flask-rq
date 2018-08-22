from setuptools import setup


install_requires = [
    "Flask-Admin",
    "hiredis",
    "raven",
    "redis",
    "rq-dashboard",
    "rq",
    "rq-scheduler",
    "statsd",
]


setup(
    name="flask_rq",
    version="1.1.0",
    description="Flask RQ",
    long_description="Flask RQ Suite",
    url="https://github.com/huangxiaohen2738/flask-rq",
    download_url="https://github.com/huangxiaohen2738/flask-rq",
    packages=["flask_rq"],
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta"
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Networking",
        "Topic :: Terminals",
        "Topic :: Utilities"
    ]
)
