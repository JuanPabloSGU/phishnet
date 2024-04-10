FROM python:alpine3.18
RUN pip install --upgrade pip
WORKDIR /app
COPY artint /app/artint
COPY gathering/utils.py /app/gathering/utils.py
COPY extract /app
RUN pip install --no-cache -r requirements.txt
CMD [ "python", "/app/features.py" ]
