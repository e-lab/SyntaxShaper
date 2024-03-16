from setuptools import setup, find_packages


def parse_requirements(filename: str) -> typing.List[str]:
    """
    Load requirements from a pip requirements file
    :param: filename - name of the requirements file to be parsed
    :return: list - list of modules mentioned in the requirements file
    """
    line_iter = (line.strip() for line in open(filename))
    return [line for line in line_iter if line and not line.startswith("#")]

requirements = [ir for ir in parse_requirements("requirements.txt")]

setup(
    name='parsechain',
    version='0.1.0',
    author='AkshathRaghav',
    author_email='araviki@purdue.edu',
    description='Ensuring parsability of LLM responses in agent chains',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AkshathRaghav/parsechain',
    install_requires=requirements,
    packages=find_packages(),
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
