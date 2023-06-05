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
    asyncio==3.4.3 \
    fastapi==0.74 \
    requests==2.28.1  \
    schedule==1.1.0 \
    watchdog==2.1.9 \
    Werkzeug==2.2.2 \
    Jinja2==3.1.2 \
    boto3==1.26.130 \
    osais>=1.0.0 \
    python-multipart==0.0.6 \
    uvicorn[standard]==0.17

# NVIDIA specials
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility

# Set the environment variables
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64
ENV PATH /usr/local/nvidia/bin:$PATH

# install out app in src/app (and we will then map volume there)
RUN mkdir -p ./app
WORKDIR /src/app

# copy files
RUN mkdir -p ./static
RUN mkdir -p ./templates
RUN chown -R root:root ./static
RUN chown -R root:root ./templates

COPY ./static/* ./static
COPY ./templates/* ./templates
COPY ./osais.json .
COPY ./ping.json .
COPY ./_ping.py .
COPY ./main_fastapi.py .
COPY ./osais_debug.py .

# ensure we upgrade osais lib
RUN  pip3 install osais --upgrade

# prepare for mounting images
RUN mkdir -p ./_input
RUN mkdir -p ./_output
RUN chown -R root:root ./_input
RUN chown -R root:root ./_output

# copy an image for warmup test
COPY ./static/warmup.jpg ./_input/warmup.jpg

# overload config with those default settings
ENV USERNAME=3fbe53cba18a5c73c3b69421e4f44812460c2e55b7634a77006e54e3f5605a3b
ENV IS_LOCAL=False
ENV IS_VIRTUALAI=True
ENV ENGINE=ping

# run as a server
CMD ["uvicorn", "main_fastapi:app", "--host", "0.0.0.0", "--port", "5001"]
