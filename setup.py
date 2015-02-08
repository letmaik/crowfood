from setuptools import setup, find_packages

setup(
    name = 'crowfood',
    description = 'C/C++ dependency graphing using snakefood',
    long_description = open('README.rst').read(),
    version = '0.2.1',
    author = 'Maik Riechert',
    author_email = 'maik.riechert@arcor.de',
    url = 'https://github.com/neothemachine/crowfood',
    classifiers=[
      'Development Status :: 4 - Beta',
      'Natural Language :: English',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3',
      'Operating System :: OS Independent',
    ],
    packages = find_packages(exclude=['crowfood.test']),
    install_requires=['six'],
    entry_points = {
        'console_scripts': [
            'cfood = crowfood.cli:main',
        ]
    }
)