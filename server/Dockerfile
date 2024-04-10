FROM python:3.12.3-slim-bookworm
WORKDIR /app
ADD . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
ENV FLASK_APP=phishnet/__init__.py
CMD ["flask", "run", "--host=0.0.0.0"]
