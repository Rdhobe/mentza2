FROM python:3.9-slim

WORKDIR /app
COPY . /app
RUN ["chmod", "+x", "start.sh"]
RUN pip install -r requirements.txt

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]