import requests
from bs4 import BeautifulSoup

# Imdb_url 전처리
def extract_code(texts):
    text = texts.split('/')
    return text[2] if len(text) > 2 else text[0]


# Imdb 사이트에서 영화 세부정보 추출(개봉년도/시청연령/장르)
def find_film_info(data):
    url = 'https://www.imdb.com/title/' + data
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})  # user-agent 설정
    elem1, elem2, elem3, genre1, genre2, genre3 = '', '', '', '', '', ''

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        element1 = soup.select(
            'ul.ipc-inline-list.ipc-inline-list--show-dividers.sc-7f1a92f5-4.kIoyyw.baseAlt li')  # 개봉년도/시청연령/시청시간
        element2 = soup.select('a.ipc-chip.ipc-chip--on-baseAlt span')  # 장르(최대 3개로 구분)

        # 경우에 따라서 추출되는 정보가 3개 미만일 수 있으므로 if 문으로 조건 설정한다.
        elem1 = element1[0].get_text() if 0 < len(element1) else ''
        elem2 = element1[1].get_text() if 1 < len(element1) else ''
        elem3 = element1[2].get_text() if 2 < len(element1) else ''

        genre1 = element2[0].get_text() if 0 < len(element2) else ''
        genre2 = element2[1].get_text() if 1 < len(element2) else ''
        genre3 = element2[2].get_text() if 2 < len(element2) else ''

    else:
        return elem1, elem2, elem3, genre1, genre2, genre3

    return elem1, elem2, elem3, genre1, genre2, genre3


# Imdb 사이트 - 개봉년도 element 추출
def find_year(data1, data2, data3):  # 개봉년도 특징: 4글자의 숫자로 구성

    if data1.isdigit() and len(data1) == 4:
        return data1

    elif data2.isdigit() and len(data2) == 4:
        return data2

    elif data3.isdigit() and len(data3) == 4:
        return data3

    return ''


# Imdb 사이트 - 시청연령 element 추출
def find_age(data1, data2, data3):  # 연령정보 특징: 4글자 미만의 숫자로 구성

    if data1.isdigit() and len(data1) < 4:
        return data1

    elif data2.isdigit() and len(data2) < 4:
        return data2

    elif data3.isdigit() and len(data3) < 4:
        return data3

    return ''


# Imdb 사이트 - 시청시간 element 추출
def find_time(data1, data2, data3):  # 시간정보 특징: hm으로 시간 구분(ex.1h 30m)

    if 'h' in data1 or 'm' in data1:
        return data1

    elif 'h' in data2 or 'm' in data2:
        return data2

    elif 'h' in data3 or 'm' in data3:
        return data3

    return ''