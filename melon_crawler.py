import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta

# 깃허브 시크릿(Secrets)에서 환경 변수 가져오기
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 토큰 또는 챗 ID가 설정되지 않았습니다.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

def crawl_melon_new_entries():
    url = "https://www.melon.com/chart/day/index.htm"
    # 멜론 차단 우회를 위한 User-Agent 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # lst50(1~50위), lst100(51~100위) 테이블 행 모두 가져오기
    songs = soup.select('tbody > tr')
    
    new_entries = []
    
    for song in songs:
        # '새로 진입' 요소가 있는지 확인
        rank_wrap = song.select_one('.rank_wrap')
        if rank_wrap and '새로 진입' in rank_wrap.get('title', ''):
            rank = song.select_one('span.rank').text
            title = song.select_one('div.ellipsis.rank01 a').text
            artist = song.select_one('div.ellipsis.rank02 span a').text
            
            new_entries.append(f"* {rank}위 (NEW) : {title} - {artist}")
            
    return new_entries

if __name__ == "__main__":
    new_songs = crawl_melon_new_entries()
    
    # 어제 날짜 구하기 (일간 차트는 보통 전일 기준)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y년 %m월 %d일")
    
    message = f"🔔 **[멜론 일간차트 신규 진입 곡]**\n기준일: {yesterday}\n\n"
    
    if new_songs:
        message += "\n".join(new_songs)
    else:
        message += "오늘은 차트에 새로 진입한 곡이 없습니다."
        
    message += "\n\n🔗 [차트 확인하기](https://www.melon.com/chart/day/index.htm)"
    
    send_telegram_message(message)
    print("크롤링 및 알림 전송 완료!")
