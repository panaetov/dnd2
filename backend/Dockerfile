FROM python:3.10

ARG NEXUS_PYPI_INDEX_URL

ENV HOME="/dude"
ENV PYTHONPATH=$HOME/source:$PYTHONPATH

RUN groupadd -g 999 dudes && \
    useradd -u 999 -m -g dudes -s /bin/bash dude && \
    mkdir -p ${HOME}

WORKDIR ${HOME}

COPY --chown=dude:dudes ./server.py ${HOME}
COPY --chown=dude:dudes ./database.py ${HOME}
COPY --chown=dude:dudes ./settings.py ${HOME}
COPY --chown=dude:dudes ./entrypoints.sh ${HOME}/entrypoints.sh
COPY --chown=dude:dudes ./requirements.txt ${HOME}/requirements.txt

RUN pip install -i "${NEXUS_PYPI_INDEX_URL:-https://pypi.org/simple}" -r "$HOME/requirements.txt"

USER dude
ENTRYPOINT ["/dude/entrypoints.sh"]
CMD ["help"]
