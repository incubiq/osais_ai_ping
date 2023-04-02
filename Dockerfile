##
##      To build the AI_PING docker image
##

# base stuff
FROM nvidia/cuda:11.7.0-base-ubuntu20.04

USER root
WORKDIR /src

ENV DEBIAN_FRONTEND=noninteractive 
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install necessary libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev \
    python3-pip \
    python3-setuptools \
    build-essential \
    cmake \
    git \
    curl \
    ca-certificates \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libatlas-base-dev \
    gfortran \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 


# Upgrade pip and install necessary Python packages
RUN pip3 install --upgrade pip
RUN pip3 install \
    numpy \
    scipy \
    scikit-learn \
    pandas \
    matplotlib \
    pillow \
    tensorflow

# install flas and various files for running host
RUN pip3 install \
    flask==2.2.2 \
    requests==2.28.1  \
    schedule==1.1.0 \
    watchdog==2.1.9 \
    Werkzeug==2.2.2 

# NVIDIA specials
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Set the environment variables
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64
ENV PATH /usr/local/nvidia/bin:$PATH

# install out app in src/app (and we will then map volume there)
RUN mkdir -p ./app
WORKDIR /src/app

COPY . .

# prepare for mounting images
RUN rm -r ./_input
RUN rm -r ./_output
RUN mkdir -p ./_input
RUN mkdir -p ./_output
RUN chown -R root:root ./_input
RUN chown -R root:root ./_output

# this is our entry point for the app
ENV FLASK_APP=flask_5000.py

# probably not needed...
EXPOSE 8080
EXPOSE 8000

# because it s flask, it will run on port 5000... but we will redirect to another port when we docker run it
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
