FROM python:3.12.10-bullseye

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "/app.py"]
