from flask import Flask, request, abort
from waitress import serve

import hmac
import hashlib
from datetime import datetime
import requests
import json
from bs4 import BeautifulSoup
import logging
import traceback

from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError

import config

app = Flask(__name__)


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(config.config["news"]["line.access.token"])
        self.handler = WebhookHandler(config.config["news"]["line.channel.secret"])

    def send_message(self, title, msg):
        try:
            self.line_bot_api.push_message(
                config.config["news"]["line.user.id"],
                TextSendMessage(text=f"Your daily news: {title}\nLink: {msg}"),
            )
            return "OK"
        except:
            return "error"

    def reply(self, reply_token, text):
        try:
            # can reply multiple messages
            self.line_bot_api.reply_message(
                reply_token=reply_token, messages=[TextSendMessage(text=text)]
            )
            return "OK"
        except:
            return "error"


@app.route("/pushnews")
def getNews():
    resp = requests.get(config.config["news"]["request.url"])
    soup = BeautifulSoup(resp.text, "html.parser")

    news_link = soup.find("a", class_="teaser__link").get("href")
    news_title = (
        soup.find("a", class_="teaser__link").select_one(".teaser__headline").text
    )

    news_link = config.config["news"]["request.url"] + news_link
    resp = requests.get(news_link)

    paragraphs = []
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("p", class_="textabsatz"):
        paragraphs.append(a.get_text())

    send_save_request(news_title.replace('"', ''), "\n".join(paragraphs).strip())

    linebot = LineBot()
    return linebot.send_message(news_title, news_link)


@app.route("/callback", methods=["POST"])
def receive_message():
    body_str = request.get_data(as_text=True)
    body = json.loads(body_str)
    timestamp = datetime.now().strftime("%Y-%m-%D %H:%M:%S")
    try:
        signature = request.headers["X-Line-Signature"]

        data = {"token": signature, "text": body["events"][0]["message"]["text"], "timestamp": datetime.now().strftime("%Y-%m-%D %H:%M:%S")}
        # print (config.config["app"]["analyzer.key"])
        key = config.config["app"]["analyzer.key"].encode(encoding = 'UTF-8')
        

        linebot = LineBot()
        linebot.handler.handle(body_str, signature)


        analyzer_signature = hmac.new(
            key=key,
            msg=f"{timestamp}{signature}".encode(encoding = 'UTF-8'),
            digestmod=hashlib.sha1,
        ).hexdigest()
        resp = requests.post(
            f"{config.config['analyzer']['host']}:{config.config['analyzer']['port']}{config.config['analyzer']['ask.bot.url']}",
            headers={
                "X-Line-Signature": signature,
                "Analyzer-Signature": analyzer_signature,
            },
            json=data,
        )
        
        # should use reply tokens as soon as possible
        linebot.reply(
            body["events"][0]["replyToken"], resp.text
        )
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    except Exception as e:
        logging.error(traceback.format_exc())
        return "error"
    logging.info(resp)
    return "OK"


def send_save_request(title, content):
    data = {"title": title, "content": content}
    try:
        resp = requests.post(
            f"{config.config['analyzer']['host']}:{config.config['analyzer']['port']}{config.config['analyzer']['send.save.url']}",
            json=data,
        )
    except Exception as e:
        logging.error(traceback.format_exc())
        return "error"
    logging.info(resp)
    return "OK"


@app.route("/", methods=["GET"])
def home():
    return "Welcome to Ginny bot"


if __name__ == "__main__":
    serve(app, host=config.config["app"]["host"], port=config.config["app"]["port"])
