import requests
import time
from bs4 import BeautifulSoup

# 넷플릭스 타이틀을 기준으로 IMDB 사이트 페이지의 url 주소 찾기
def find_imdb_url(data):
    title = data
    find_url = ''

    url = 'https://www.imdb.com/find/?q=' + title + '&s=tt&exact=true'
    time.sleep(2)

    session = requests.Session()  # cookie 기록을 남겨서 scraper 차단 방지
    response = session.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})  # user-agent 설정(cookie 기록 남겨서 크롤링 차단 방지)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")  # HTML 문서 가져오기
        elements = soup.find('div', class_='ipc-metadata-list-summary-item__tc')

        if elements:
            links = elements.find_all('a')
            href_list = [link.get('href') for link in links]

            for href in href_list:
                if 'title/' in href:
                    find_url = href
                    break

                else:
                    pass

    else:
        find_url = ''

    return find_url


# 가장 최상단에 검색되는 imdb 사이트 주소의 코드 맵핑
def search_google(data):
    title = data
    url = 'https://www.google.com/search?q=' + data + '+netflix+imdb'
    time.sleep(2)

    session = requests.Session()  # cookie 기록을 남겨서 scraper 차단 방지
    response = session.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})  # user-agent 설정

    imdb_link = ""

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")  # HTML 문서 가져오기
        links = soup.find_all('a')

        for link in links:
            href = link.get('href')

            # 가장 먼저 검색되는 imdb 사이트 맵핑
            if href and 'https://www.imdb.com/title' in href:
                imdb_link = href[href.find('title') - 1:]
                break

    else:
        return imdb_link

    return imdb_link


# Imdb 사이트에서 영화 재검색
def refind_imdb_url(title, year):
    find_url = ''
    url = 'https://www.imdb.com/find/?q=' + title + '&s=tt&exact=true'
    time.sleep(1)

    session = requests.Session()  # cookie 기록을 남겨서 scraper 차단 방지
    response = session.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})  # user-agent 설정

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")  # HTML 문서 가져오기

        try:
            elements = soup.find_all('div', class_='ipc-metadata-list-summary-item__tc')

            if len(elements) > 0:
                # 검색된 동명 프로그램에서 년도가 일치하는 프로그램의 IMDB 주소 맵핑
                for index in range(len(elements)):
                    imdb_year = elements[index].find(class_='ipc-metadata-list-summary-item__li').get_text()  # 년도정보

                    if imdb_year == year:
                        find_url = elements[index].find(class_='ipc-metadata-list-summary-item__t').get('href')
                        break

                    else:
                        pass

            else:
                find_url = ''

        except:
            pass

    return find_url


# Imdb 사이트에서 영화 재검색 - 정확한 타이틀 검색명으로 안나오는 경우
def refind_imdb_url_noexact(title, year):
    find_url = ''
    url = 'https://www.imdb.com/find/?q=' + title
    time.sleep(0.5)

    session = requests.Session()  # cookie 기록을 남겨서 scraper 차단 방지
    response = session.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'})  # user-agent 설정

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")  # HTML 문서 가져오기

        try:
            elements = soup.find_all('div', class_='ipc-metadata-list-summary-item__tc')

            if len(elements) > 0:
                # 검색된 동명 프로그램에서 년도가 일치하는 프로그램의 IMDB 주소 맵핑
                for index in range(len(elements)):
                    imdb_year = elements[index].find(class_='ipc-metadata-list-summary-item__li').get_text()  # 년도정보

                    if int(imdb_year) == int(year):
                        find_url = elements[index].find(class_='ipc-metadata-list-summary-item__t').get('href')
                        break

                    else:
                        pass

            else:
                find_url = ''

        except:
            pass

    return find_url

