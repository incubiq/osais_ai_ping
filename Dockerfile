##
##      To build the AI_PING docker image
##

# base stuff
FROM yeepeekoo/public:ai_base_osais


###### update latest OSAIS config ######

# push again the base files
COPY ./_static/* ./_static
COPY ./_templates/* ./_templates
COPY ./_osais/* .

# copy warmup files
COPY ./_input/warmup.jpg ./_input/warmup.jpg


###### specific AI config ######

# keep ai in its directory (this includes config files)
COPY ./ai ./ai

# overload config with those default settings
ENV ENGINE=ping

# run as a server
CMD ["uvicorn", "main_fastapi:app", "--host", "0.0.0.0", "--port", "5001"]
