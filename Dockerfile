FROM ubuntu:22.04

ARG PYTHON_VERSION_TAG=3.12
ARG LINK_PYTHON_TO_PYTHON3=1

ENV POETRY_NO_INTERACTION=1 
ARG DEBIAN_FRONTEND=noninteractive 
ARG GROUP_ID
ARG USER_ID
RUN addgroup --gid ${GROUP_ID} notarygroup
RUN adduser --disabled-password --gecos '' --uid ${USER_ID} --gid ${GROUP_ID} komodian
RUN apt update && apt install software-properties-common -y && add-apt-repository ppa:deadsnakes/ppa

RUN apt-get -qq -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get -qq -y install \
        gcc \
        curl \
        nano \
        htop \
        python3.12 \
        python3.12-dev \
        python3.12-distutils \
        python3.12-venv \
        build-essential \
        postgresql \
        postgresql-contrib \
        sqlite3 \
        python-is-python3 \
        libpq-dev \
        software-properties-common \
        libmysqlclient21 \
        pkg-config \
        libmysqlclient-dev
        
#    mv /usr/bin/lsb_release /usr/bin/lsb_release.bak && \
#    apt-get -y autoclean && \
#    apt-get -y autoremove && \
#    rm -rf /var/lib/apt/lists/*

RUN rm /usr/bin/python3 && ln -s /usr/bin/python3.12 /usr/bin/python3
# Setup user and working directory

RUN chown -R komodian:notarygroup /home/komodian
USER komodian
WORKDIR /home/komodian/api
RUN mkdir /home/komodian/poetry
RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN python3.12 -m pip install -U pip
ENV POETRY_HOME="/home/komodian/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
ENV IN_DOCKER=True
COPY ./pyproject.toml /home/komodian/api/
RUN curl -sSL https://install.python-poetry.org | python
RUN poetry self update
RUN poetry env use /usr/bin/python3.12
RUN poetry lock && poetry install


