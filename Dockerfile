FROM python:3-alpine

RUN apk add zlib-dev jpeg-dev gcc musl-dev

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["application.py"]
