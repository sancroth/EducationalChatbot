FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x ./entrypoint.sh &&\
    python -m spacy download el_core_news_md &&\
    rasa train --force

EXPOSE 5005
EXPOSE 5055

ENTRYPOINT ["./entrypoint.sh"]