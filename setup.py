from setuptools import setup, find_packages

setup(
  name='constrain',
  version='0.1.0',
  author='Akshath Raghav',
  author_email='araviki@purdue.edu',
  description='Constrain helps supercharge agent chains by ensuring parseable outputs.',
  packages=find_packages(),
  classifiers=[
  'Programming Language :: Python :: 3',
  'License :: OSI Approved :: MIT License',
  'Operating System :: OS Independent',
  ],
  python_requires='>=3.8',
)