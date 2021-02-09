
# Get xenial container
FROM osrf/ros:kinetic-desktop-full

# Install tools
RUN apt-get update \
    && apt-get -y install ssh build-essential cmake cppcheck valgrind htop\
    python python-matplotlib python-tk ffmpeg wget \
    net-tools python-pip python-flake8 flake8
RUN python -m pip install flake8 apriltag getkey

# Install reading to robot
COPY ./ReadingToRobot reading_to_robot
WORKDIR /reading_to_robot
RUN python -m pip install -e .
WORKDIR ..

# Install MDK
ARG MIRO_DIR_MDK
RUN echo $MIRO_DIR_MDK
# TODO: Add installation steps for MDK

# Clean up
RUN rosdep update \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*
