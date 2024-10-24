FROM python:alpine3.18
RUN pip install --upgrade pip
WORKDIR /app
COPY artint /app/artint
COPY utilities/ServiceUtils.py /app/utilities/ServiceUtils.py
COPY extract /app
RUN pip install --no-cache -r requirements.txt
CMD [ "python", "/app/S3Uploader.py" ]
