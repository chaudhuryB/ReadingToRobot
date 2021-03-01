import io
import os
import setuptools
import sys


with io.open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


# Install nao and miro executables in python 2 only, and cozmo in python 3 only.
if sys.version_info[0] < 3:
    scripts = [
        'readingtorobot/read_to_NAO',
        'readingtorobot/read_to_miro']
    requirementPath = './requirements2.txt'
    requires = ">=2.7"
else:
    scripts = ['readingtorobot/read_to_cozmo']
    requirementPath = './requirements3.txt'
    requires = ">=3.7"

with open(requirementPath) as f:
    install_requires = f.read().splitlines()

install_requires.append(requires)

setuptools.setup(
    name="readingtorobot",
    version="0.0.1",
    author="Aitor Miguel Blanco, Bishakha Chaudhury",
    author_email="aitormibl@gmail.com",
    description="Checking the efficacy of reading to robot as a support for teachers in engaging kids with reading.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chaudhuryB/ReadingToRobot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    scripts=scripts,
    python_requires=install_requires,
)
