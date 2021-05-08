import requests
from bs4 import BeautifulSoup
import configparser

req_url = ""

def getNews():
  loadConfig()
  resp = requests.get(req_url)
  soup = BeautifulSoup(resp.text, "html.parser")
  news_link = soup.find("a", class_="teaser__link").get("href") #只搜尋第一個符合條件的HTML節點, class為teaser__link的, 取href的值
  paragraph = soup.find("a", class_="teaser__link")
  news_title = paragraph.select_one(".teaser__headline").text


def loadConfig(): 
  global req_url
  config = configparser.ConfigParser()
  config.read('service.conf')
  req_url = config['news']['request.url']

if __name__ == '__main__':
  getNews()