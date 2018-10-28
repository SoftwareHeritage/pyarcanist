import sys
from os import path
from io import open
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))
src_dir = path.join(here, "src")

# When executing the setup.py, we need to be able to import ourselves, this
# means that we need to add the src/ directory to the sys.path.
sys.path.insert(0, src_dir)

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyarc',
    version='0.0.1',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'click',
        'phabricator',
        'gitpython'],
    package_dir={"": "src"},
    packages=find_packages('src'),
    entry_points={
        'console_scripts': [
            'pyarc=pyarc.cli:pyarc']},
    )
