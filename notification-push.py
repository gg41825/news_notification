from flask import Flask, request, abort
from waitress import serve

import requests
import json
from bs4 import BeautifulSoup
import configparser
import logging
import traceback

from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(config["news"]["line.access.token"])
        self.handler = WebhookHandler(config["news"]["line.channel.secret"])

    def send_message(self, title, msg):
        try:
            self.line_bot_api.push_message(
                config["news"]["line.user.id"],
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
    resp = requests.get(config["news"]["request.url"])
    soup = BeautifulSoup(resp.text, "html.parser")

    news_link = soup.find("a", class_="teaser__link").get("href")
    news_title = soup.find("a", class_="teaser__link").select_one(".teaser__headline").text

    news_link = config["news"]["request.url"]+news_link
    resp = requests.get(news_link)

    paragraphs = []
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("p", class_="textabsatz"):
        paragraphs.append(a.get_text())

    send_save_request("test", "\n".join(paragraphs).strip())

    linebot = LineBot()
    return linebot.send_message(news_title, news_link)


@app.route("/callback", methods=["POST"])
def receive_message():
    body_str = request.get_json(as_text=True)
    try:
        body = json.loads(body_str)
        signature = request.headers["X-Line-Signature"]

        linebot = LineBot()
        linebot.handler.handle(body_str, signature)

        # should use reply tokens as soon as possible
        linebot.reply(
            body["events"][0]["replyToken"], body["events"][0]["message"]["text"]
        )
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    except:
        print(body_str)
    return "OK"


def send_save_request(title, content):
    data = {"title": title, "content": content}
    try:
        resp = requests.post(
            f"{config['analyzer']['host']}:{config['analyzer']['port']}{config['analyzer']['send_save_url']}", json=data
        )
    except Exception as e:
        logging.error(traceback.format_exc())
        return "error"
    logging.info(resp)
    return "OK"


@app.route("/", methods=["GET"])
def home():
    return "Welcome to Ginny bot"


def load_news_config():
    global config

    config = configparser.ConfigParser()
    config.read("service.conf")


if __name__ == "__main__":
    load_news_config()
    serve(app, host=config["app"]["host"], port=config["app"]["port"])