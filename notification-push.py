from flask import Flask
from waitress import serve
import requests
from bs4 import BeautifulSoup
import configparser

from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

@app.route("/pushnews")
def getNews():
    resp = requests.get(req_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    news_link = soup.find("a", class_="teaser__link").get("href") #只搜尋第一個符合條件的HTML節點, class為teaser__link的, 取href的值
    paragraph = soup.find("a", class_="teaser__link")
    news_title = paragraph.select_one(".teaser__headline").text
    try:
        line_bot_api = LineBotApi(access_token)
        line_bot_api.push_message(user_id, TextSendMessage(text=f'Your daily news: {news_title}\nLink: {req_url}{news_link}'))
        return 'OK'
    except:
        print("error")

@app.route("/", methods=['GET'])
def home():
    return 'Welcome to Ginny bot'


def loadConfig():
  global req_url, access_token, secret, user_id, host, port
  
  config = configparser.ConfigParser()
  config.read('service.conf')
  host = config['app']['host']
  port = config['app']['port']

  req_url = config['news']['request.url']
  access_token = config['news']['line.access.token']
  user_id = config['news']['line.user.id']

if __name__ == '__main__':
    loadConfig()
    serve(app, host=host, port=port)