FROM python:3.8.5-slim-buster

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 2222 80
WORKDIR /app
COPY . .
ENTRYPOINT ["python3", "/app/main.py"]
CMD ["2001"]
