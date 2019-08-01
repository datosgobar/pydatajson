#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import os

with open(os.path.abspath('README.md')) as readme_file:
    readme = readme_file.read()

with open(os.path.abspath('HISTORY.md')) as history_file:
    history = history_file.read()

with open(os.path.abspath("requirements.txt")) as f:
    requirements = [req.strip() for req in f.readlines()]

with open(os.path.abspath("requirements_dev.txt")) as f:
    test_requirements = [req.strip() for req in f.readlines()]

with open(os.path.abspath("requirements_2.7.txt")) as f:
    backport_requirements = [req.strip() for req in f.readlines()]

setup(
    name='pydatajson',
    version='0.4.44',
    description="Paquete en python con herramientas para generar y validar metadatos de catálogos de datos en formato data.json.",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    author="Datos Argentina",
    author_email='datos@modernizacion.gob.ar',
    url='https://github.com/datosgobar/pydatajson',
    packages=[
        'pydatajson',
    ],
    package_dir={'pydatajson':
                 'pydatajson'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='pydatajson',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
        ':python_version=="2.7"': backport_requirements
    },
    entry_points={
        'console_scripts': [
            'pydatajson = pydatajson.__main__:main'
        ]
    }
)
