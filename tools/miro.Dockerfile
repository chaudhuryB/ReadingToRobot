
ARG ARCH=arm64v8
# Get xenial container
FROM $ARCH/ros:kinetic-perception

# Install tools
RUN apt-get update \
    && apt-get -y install ssh build-essential cmake cppcheck valgrind htop\
    python python-matplotlib python-tk ffmpeg wget \
    net-tools python-pip python-flake8 flake8
RUN python -m pip install flake8 apriltag getkey

# Install reading to robot
COPY . reading_to_robot
WORKDIR /reading_to_robot
RUN python -m pip install -e .

# Install MDK (Warning, you need to download the MDK in the ReadingToRobot folder for this to work)
WORKDIR ./mdk/bin/arm32
RUN ./install_mdk.sh

# Clean up
WORKDIR /
RUN rosdep update \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*
