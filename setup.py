from setuptools import setup, find_packages

setup(
    name = 'crowfood',
    version = '0.1.0',
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