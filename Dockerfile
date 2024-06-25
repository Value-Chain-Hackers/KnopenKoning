FROM python:3.11.9-bookworm

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY config.py  /app/config.py
COPY db         /app/db
COPY jobs       /app/jobs
COPY data       /app/data
COPY backend    /app/backend
COPY prompts    /app/prompts
COPY utils      /app/utils
COPY ontologies /app/ontologies


WORKDIR /app
EXPOSE 18000 11434
ENTRYPOINT [ "python", "backend/main.py" ]
