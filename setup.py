#
# Setup file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import pathlib
from setuptools import find_packages, setup

# A good example of how to build a Python package can be found here: https://realpython.com/pypi-publish-python-package/


# Find the package root directory.
PACKAGE_DIR = pathlib.Path(__file__).parent

# Set up the package.
# @formatter:off
setup(
    name='fusion-platform-python-sdk',
    version='1.17.5',
    description='Python SDK used to interact with the Fusion Platform(r)',
    long_description=(PACKAGE_DIR / 'README.md').read_text(),
    long_description_content_type='text/markdown',
    url='https://github.com/d-cat-support/fusion-platform-python-sdk',
    author='Digital Content Analysis Technology Ltd',
    author_email='support@d-cat.co.uk',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    packages=find_packages(exclude='tests'),
    include_package_data=True,
    install_requires=[
        'marshmallow',
        'pathos',
        'prompt_toolkit',
        'pyjwt',
        'python-dateutil',
        'python-i18n[YAML]',
        'requests',
        'tenacity',
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'fusion_platform=fusion_platform.command:main',
        ]
    }
)
# @formatter:on
