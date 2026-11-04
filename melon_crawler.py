import requests
from bs4 import BeautifulSoup
import os
import sys
from datetime import datetime, timedelta
import random

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(text):
    """전송 성공 여부를 True/False로 반환. 실패 시 텔레그램 응답 본문을 로그에 남김."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 토큰 또는 챗 ID가 설정되지 않았습니다.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # parse_mode 제거: 곡명/가수명의 _ * [ ` 때문에 Markdown 파싱 오류(400)가 나는 것을 방지
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'disable_web_page_preview': True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if not response.ok:
            print(f"텔레그램 전송 실패: HTTP {response.status_code} / {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"텔레그램 메시지 전송 실패: {e}")
        return False

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    return random.choice(user_agents)

def is_new_entry(song):
    """신규 진입 여부 판별.
    현재 멜론 구조: <span class="bullet_icons rank_new"><span class="none">순위 진입</span></span>
    (예전 구조: .rank_wrap 의 title='새로 진입' 도 함께 지원)
    """
    if song.select_one('.rank_new'):
        return True
    rank_wrap = song.select_one('.rank_wrap')
    if rank_wrap and '진입' in rank_wrap.get('title', ''):
        return True
    return False

def crawl_melon_new_entries():
    url = "https://www.melon.com/chart/day/index.htm"
    headers = {
        "User-Agent": get_random_user_agent()
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return [f"⚠️ 멜론 페이지 접근 실패: HTTP 요청 에러 발생\n상세: {e}"]

    soup = BeautifulSoup(response.text, 'html.parser')
    songs = soup.select('tbody > tr')

    if not songs:
        return ["⚠️ 크롤링 에러: 테이블에서 곡 정보를 찾을 수 없습니다. (HTML 구조 변경 또는 차단 의심)"]

    new_entries = []

    for song in songs:
        try:
            if not is_new_entry(song):
                continue

            rank_elem = song.select_one('span.rank')
            title_elem = song.select_one('div.ellipsis.rank01 a')
            artist_elem = song.select_one('div.ellipsis.rank02 a')

            rank = rank_elem.text.strip() if rank_elem else "?"
            title = title_elem.text.strip() if title_elem else "(곡명 파싱 실패)"
            artist = artist_elem.text.strip() if artist_elem else "(가수 파싱 실패)"
            # 파싱이 일부 실패해도 버리지 않고 표시
            new_entries.append(f"* {rank}위 (NEW) : {title} - {artist}")
        except Exception as e:
            print(f"곡 정보 파싱 중 에러: {e}")
            continue

    print(f"전체 {len(songs)}곡 중 신규 진입 {len(new_entries)}곡")
    return new_entries

if __name__ == "__main__":
    new_songs = crawl_melon_new_entries()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y년 %m월 %d일")

    message = f"🔔 [멜론 일간차트 신규 진입 곡]\n기준일: {yesterday}\n\n"

    if new_songs:
        message += "\n".join(new_songs)
    else:
        message += "오늘은 차트에 새로 진입한 곡이 없습니다."

    message += "\n\n🔗 차트 확인하기: https://www.melon.com/chart/day/index.htm"

    if send_telegram_message(message):
        print("크롤링 및 알림 전송 완료!")
    else:
        print("알림 전송 실패 - 위 로그 확인")
        sys.exit(1)  # 실패를 Actions에서 빨간불로 보이게 함
