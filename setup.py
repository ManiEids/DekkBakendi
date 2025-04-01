from setuptools import setup, find_packages
import glob
import os

# Get all spider files for inclusion
spider_files = glob.glob('Leita/spiders/*.py')
spider_files.extend(glob.glob('Leita/Leita/spiders/*.py'))

setup(
    name="Leita",
    version="0.1",
    packages=find_packages(),
    package_data={
        'Leita': ['spiders/*.py'],
        '': ['*.json']  # Include any JSON files in the package
    },
    include_package_data=True,
    install_requires=[
        "scrapy",
        "flask",
        "gunicorn",
        "python-dotenv"
    ],
)
