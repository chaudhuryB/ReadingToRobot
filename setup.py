import io
import setuptools


with io.open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


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
    scripts=[
        'readingtorobot/read_to_cozmo',
        'readingtorobot/read_to_NAO',
        'readingtorobot/read_to_miro'
    ],
    python_requires='>=3.7',
)
