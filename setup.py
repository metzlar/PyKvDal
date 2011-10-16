"""
Python Key Value DAL
--------------

Simple pure python Key Value Data Abstraction Layer

"""
from setuptools import setup
import sys

if 'register' in sys.argv or 'upload' in sys.argv:
    raise Exception('I don\'t want to be on PyPI (yet)!')

setup(
    name='PyKvDal',
    version='0.1',
    license='BSD',
    author='Ivan Metzlar',
    author_email='metzlar@gmail.com',
    description='Simple Key Value Data Abstraction Layer',
    long_description=__doc__,
    py_modules=['pykvdal'],
    test_suite='nose.collector',
    zip_safe=False,
    platforms='any',
    include_package_data=True,
    tests_require=[
        'nose',
        'PyContracts',
        'python-memcached',
        'coverage'
    ],
)
