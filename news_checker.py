from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import csv
import telegram
import config


def change_date_format(date):
    """
    날짜 포맷을 년.월.일. 형식으로 변경하는 함수
    네이버 뉴스의 경우
    0분전, 0시간 전, 0일전 등 7일 내 뉴스는
    년.월.일이 아닌 다른 포맷으로 표시되므로 날짜를 통일해주는 함수가 필요함
    """
    current_time = datetime.now()
    date = date.replace(" ", "")
    if date.endswith('분전'):
        minutes = int(date[:-2])
        date = current_time - timedelta(minutes=minutes)

    elif date.endswith('시간전'):
        hours = int(date[:-3])
        date = current_time - timedelta(hours=hours)

    elif date.endswith('일전'):
        days = int(date[:-2])
        date = current_time - timedelta(days=days)

    else:
        date = datetime.strptime(date, '%Y.%m.%d.')
    return date.strftime("%Y-%m-%d")


ua = UserAgent()
useragent = ua.random
query = ''

params = {
    'where': 'news',
    'query': query,
    'sm': 'tab_srt',
    'sort': 1,
    'photo': 0,
    'field': 0,
    'reporter_article': '',
    'pd': 0,
    'ds': '',
    'de': '',
    'docid': '',
    'nso': 'so:dd,p:all,a:all',
    'mynews': 0,
    'start': 1,
    'refresh_start': 0,
    'related': 0
}


bot = telegram.Bot(token=config.telegram_token)

base_url = 'https://search.naver.com/search.naver?'
req = requests.get(base_url, params=params, headers={'User-Agent': useragent})
soup = BeautifulSoup(req.text, 'html.parser')

news_list = soup.select('div.group_news div.news_area')
results = []
fr = open('news.csv', 'r')
csv_reader = csv.reader(fr)
recent_news = [row[4] for row in csv_reader][-1]

# publishing_company 갯수가 2개 이상이면, 언론사와 네이버 뉴스 2곳에 보도된 기사임.
# csv 파일과 네이버 뉴스 크롤링 순서가 반대라서 한가지로 통일하기 위해 크롤링 한 파일을 저장한 리스트를 csv에 저장하기 전에 순서를 뒤집어줌
with open('news.csv', 'a', newline='') as fw:
    csv_writer = csv.writer(fw)
    for news in news_list:
        publishing_company = news.select('a.info')
        date = change_date_format(news.select_one('span.info').text)
        is_published = publishing_company[1]['href'] \
            if len(publishing_company) > 1 else None
        title = news.select_one('a.news_tit')['title']
        url = news.select_one('a.news_tit')['href']
        description = news.select_one('a.api_txt_lines.dsc_txt_wrap').text
        if url == recent_news:
            bot.sendMessage(chat_id=config.chat_id, text="최신 기사가 이미 저장되어 있기 때문에 종료합니다.")
            break
        results.append([publishing_company[0].text, date, is_published, title, url, description])
        bot.sendMessage(chat_id=config.chat_id, text="""[{0}]\n {1}의 기사 1건이 보도되었습니다.\n title : {2} \n url :{3}""".format(date, publishing_company[0].text, title, url))
    results.reverse()
    csv_writer.writerows(results)

fr.close()
