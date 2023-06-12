##
##      To build the AI_PING docker image
##

# base stuff
FROM yeepeekoo/public:ai_base

WORKDIR /src/app

# install requirements

# keep ai in its directory
RUN mkdir -p ./ai
RUN chown -R root:root ./ai
COPY ./ai/runai.py ./ai/runai.py

# copy AI
COPY ./ping.json .
COPY ./_ping.py .

# overload config with those default settings
ENV USERNAME=3fbe53cba18a5c73c3b69421e4f44812460c2e55b7634a77006e54e3f5605a3b
ENV IS_LOCAL=False
ENV IS_VIRTUALAI=True
ENV ENGINE=ping

# run as a server
CMD ["uvicorn", "main_fastapi:app", "--host", "0.0.0.0", "--port", "5001"]
