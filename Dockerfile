FROM python:3-alpine

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["application.py"]
