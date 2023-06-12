from flask import Flask, request, abort
from waitress import serve

import requests
import json
from bs4 import BeautifulSoup
import configparser

from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi(access_token)
        self.handler = WebhookHandler(channel_secret)

    def send_message(self, title, msg):
        try: 
            self.line_bot_api.push_message(user_id, TextSendMessage(text=f'Your daily news: {title}\nLink: {req_url}{msg}'))
            return "OK"
        except:
            return "error"
        
    def reply(self, reply_token, text):
        try:
            # can reply multiple messages
            self.line_bot_api.reply_message(reply_token=reply_token, messages=[TextSendMessage(text=text)])
            return "OK"
        except:
            return "error"


@app.route("/pushnews")
def getNews():
    resp = requests.get(req_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    news_link = soup.find("a", class_="teaser__link").get("href") #只搜尋第一個符合條件的HTML節點, class為teaser__link的, 取href的值
    paragraph = soup.find("a", class_="teaser__link")
    news_title = paragraph.select_one(".teaser__headline").text
    linebot = LineBot()
    return linebot.send_message(news_title, news_link)
    

@app.route("/callback", methods=['POST'])
def receive_message():
    body_str = request.get_data(as_text=True)
    try:
        body = json.loads(body_str)
        linebot = LineBot()
        signature = request.headers['X-Line-Signature']
        linebot.handler.handle(body_str, signature)
        
        # should use reply tokens as soon as possible
        linebot.reply(body['events'][0]['replyToken'], body['events'][0]['message']['text'])
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except:
        print(body_str)
    return 'OK'


@app.route("/", methods=['GET'])
def home():
    return 'Welcome to Ginny bot'


def load_news_config():
    global req_url, access_token, channel_secret, user_id, host, port
  
    config = configparser.ConfigParser()
    config.read('service.conf')
    host = config['app']['host']
    port = config['app']['port']

    req_url = config['news']['request.url']
    access_token = config['news']['line.access.token']
    user_id = config['news']['line.user.id']
    channel_secret = config['news']['line.channel.secret']


if __name__ == '__main__':
    load_news_config()
    serve(app, host=host, port=port)