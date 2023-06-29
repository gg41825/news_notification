FROM python:3.10
WORKDIR ./news_notification
ADD . .
RUN pip install -r requirements.txt
CMD ["python", "./main.py"]
