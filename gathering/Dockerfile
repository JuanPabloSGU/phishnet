FROM python:alpine3.18
RUN pip install --upgrade pip
WORKDIR /app
COPY . /app
RUN pip install --no-cache -r requirements.txt
CMD [ "python", "main.py" ]
