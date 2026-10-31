import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import random # 추가

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
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"텔레그램 메시지 전송 실패: {e}")

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    return random.choice(user_agents)

def crawl_melon_new_entries():
    url = "https://www.melon.com/chart/day/index.htm"
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 200 OK 코드가 아닌 경우 에러 발생
    except requests.exceptions.RequestException as e:
        return [f"⚠️ 멜론 페이지 접근 실패: HTTP 요청 에러 발생\n상세: {e}"]

    soup = BeautifulSoup(response.text, 'html.parser')
    songs = soup.select('tbody > tr')
    
    if not songs:
        return ["⚠️ 크롤링 에러: 테이블에서 곡 정보를 찾을 수 없습니다. (HTML 구조 변경 또는 차단 의심)"]

    new_entries = []
    
    for song in songs:
        try:
            rank_wrap = song.select_one('.rank_wrap')
            # '새로 진입' 텍스트 기반 필터링
            if rank_wrap and '새로 진입' in rank_wrap.get('title', ''):
                rank_elem = song.select_one('span.rank')
                title_elem = song.select_one('div.ellipsis.rank01 a')
                artist_elem = song.select_one('div.ellipsis.rank02 span a')
                
                # HTML 요소가 안전하게 존재하는지 확인 후 텍스트 추출
                if rank_elem and title_elem and artist_elem:
                    rank = rank_elem.text.strip()
                    title = title_elem.text.strip()
                    artist = artist_elem.text.strip()
                    new_entries.append(f"* {rank}위 (NEW) : {title} - {artist}")
        except Exception as e:
             # 개별 곡 파싱 실패 시 로깅만 하고 계속 진행
             print(f"곡 정보 파싱 중 에러: {e}")
             continue
            
    return new_entries

if __name__ == "__main__":
    new_songs = crawl_melon_new_entries()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y년 %m월 %d일")
    
    message = f"🔔 **[멜론 일간차트 신규 진입 곡]**\n기준일: {yesterday}\n\n"
    
    if new_songs:
        message += "\n".join(new_songs)
    else:
        message += "오늘은 차트에 새로 진입한 곡이 없습니다."
        
    message += "\n\n🔗 [차트 확인하기](https://www.melon.com/chart/day/index.htm)"
    
    send_telegram_message(message)
    print("크롤링 및 알림 전송 완료!")
