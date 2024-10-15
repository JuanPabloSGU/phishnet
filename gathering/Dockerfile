FROM python:alpine3.18
RUN pip install --upgrade pip
WORKDIR /app
COPY utilities /app/utilities
COPY gathering /app
RUN pip install --no-cache -r requirements.txt
CMD [ "python", "/app/main.py" ]
