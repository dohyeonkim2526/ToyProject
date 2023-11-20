import pandas as pd
import numpy as np
import pymysql
import requests
import json
from lxml import etree
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys
import time
sys.path.insert(0, './ImdbScores') # mysql 접속정보 저장한 폴더경로 연결
import mysql_connect # mysql 접속정보

login = mysql_connect.info

# MySQL 서버 연결
conn = pymysql.connect(host = login['host'],
                       port = login['port'],
                       user = login['username'],
                       password = login['password'],
                       db = 'ImdbDB',
                       charset = login['charset'])

# MySQL 서버와 연결할 수 있는 cursor 생성
cursor = conn.cursor()


# read csv
result_df = pd.read_csv('/Users/gimdohyeon/Documents/스터디/dataset/result_df.csv')
result_df = result_df[['Imdb_code', 'Title', 'Imdb_Premiere', 'Imdb_Age', 'Imdb_Time', 'IMDB Score', 'Language', 'Nflx_Genre1', 'Nflx_Genre2', 'Nflx_Genre3', 'Nflx_Genre4']] # 컬럼 순서 변경
result_df = result_df.replace({np.nan: None})

sql = """INSERT INTO ImdbDB.films (imdb_code, title, imdb_premiere, imdb_age, imdb_time, imdb_score, imdb_language, nflx_genre1, nflx_genre2, nflx_genre3, nflx_genre4) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""


for index, row in result_df.iterrows():
    cursor.execute(sql, tuple(row))

conn.commit()

cursor.close() # cursor 닫기
conn.close() # db connection 닫기




# Imdb 사이트 크롤링
# imdb_code를 이용해서 나라별 평가 점수와 포스터 이미지 수집
country_dict = {}  # (key: imdb_code, value: imdb site's json)
poster_dict = {} # (key: imdb_code, value: poster img)
error = list()

for index, row in tqdm(result_df.iterrows(), total = result_df.shape[0]):

    code = row['Imdb_code']
    url = 'https://www.imdb.com/title/' + code + '/ratings/'
    time.sleep(2)

    session = requests.Session() # cookie 기록을 남겨서 scraper 차단 방지
    response = requests.get(url, headers = {'User-Agent' :
                                                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}) # user-agent 설정

    try:
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser').find('body')

            # html parsing
            dom = etree.HTML(str(soup)) # page로부터 html parsing
            element = dom.xpath('//*[@id="__NEXT_DATA__"]/text()')[0]  # xpath를 통해서 Json 추출

            # json
            json_object = json.loads(element)
            j_object = json_object['props']['pageProps']['contentData']  # poster image, rating 정보가 있는 부분

            # extract data from json
            poster_img = j_object['entityMetadata']['primaryImage']['url']  # films poster image
            country_data = j_object['histogramData']['countryData']  # country rates and voteCount info

            # make dict (key: imdb_code, value: imdb site's json)
            country_dict[code] = country_data
            poster_dict[code] = poster_img

    except:
        error.append(code) # rating 정보를 제공하지 않는 경우
        print('error')


# Imdb 사이트에서 수집한 정보 db upload
cursor = conn.cursor()
cursor.execute("""TRUNCATE TABLE ImdbDB.imdb_score""")
insert_sql = """INSERT INTO ImdbDB.imdb_score(imdb_code, json_data) VALUES (%s, %s)"""
update_sql = """UPDATE ImdbDB.imdb_score
                    SET poster_img = %s
                    WHERE imdb_code = %s"""


for key, value in country_dict.items(): # insert mysql with ratings info(json) and poster image
    code = key
    json_data = json.dumps(value)

    if json_data != '[]':
        values = (key, json_data)
        cursor.execute(insert_sql, values)

        img = poster_dict[code]
        cursor.execute(update_sql, (img, code))

conn.commit()


# 영화에 대해 수집한 모든 정보를 가지는 Main 테이블 생성 > Flask를 연동해서 웹페이지 보여줄 때 사용할 테이블
# JOIN - 영화정보, Json data, 포스터이미지
cursor = conn.cursor()
cursor.execute("""CREATE TABLE ImdbDB.films_info AS
                    SELECT A.imdb_code
                         , A.title
                         , A.imdb_premiere
                         , A.imdb_age
                         , A.imdb_language
                         , B.json_data
                         , B.poster_img
                    FROM ImdbDB.films AS A
                    LEFT JOIN ImdbDB.imdb_score AS B
                    ON A.imdb_code = B.imdb_code""")

conn.commit()

cursor.close()
conn.close()


# Imdb 사이트 크롤링 : imdb_code를 이용해서 나라별 평가 점수와 포스터 이미지 수집
#
# country_dict = {}  # (key: imdb_code, value: imdb site's json)
# poster_dict = {} # (key: imdb_code, value: poster img)
# error = list()
#
# for index, row in tqdm(result_df.iterrows(), total = result_df.shape[0]):
#
#     code = row['Imdb_code']
#     url = 'https://www.imdb.com/title/' + code + '/ratings/'
#     time.sleep(2)
#
#     session = requests.Session() # cookie 기록을 남겨서 scraper 차단 방지
#     response = requests.get(url, headers = {'User-Agent' :
#                                                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}) # user-agent 설정
#
#     try:
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser').find('body')
#
#             # html parsing
#             dom = etree.HTML(str(soup)) # page로부터 html parsing
#             element = dom.xpath('//*[@id="__NEXT_DATA__"]/text()')[0]  # xpath를 통해서 Json 추출
#
#             # json
#             json_object = json.loads(element)
#             j_object = json_object['props']['pageProps']['contentData']  # poster image, rating 정보가 있는 부분
#
#             # extract data from json
#             poster_img = j_object['entityMetadata']['primaryImage']['url']  # films poster image
#             country_data = j_object['histogramData']['countryData']  # country rates and voteCount info
#
#             # make dict (key: imdb_code, value: imdb site's json)
#             country_dict[code] = country_data
#             poster_dict[code] = poster_img
#
#     except:
#         error.append(code) # rating 정보를 제공하지 않는 경우
#         print('error')


# db upload
# cursor = conn.cursor()
# cursor.execute("""TRUNCATE TABLE ImdbDB.imdb_score""")
# insert_sql = """INSERT INTO ImdbDB.imdb_score(imdb_code, json_data) VALUES (%s, %s)"""
# update_sql = """UPDATE ImdbDB.imdb_score
#                     SET poster_img = %s
#                     WHERE imdb_code = %s"""


# insert mysql with ratings info(json) and poster image
# for key, value in country_dict.items():
#     code = key
#     json_data = json.dumps(value)
#
#     if json_data != '[]':
#         values = (key, json_data)
#         cursor.execute(insert_sql, values)
#
#         img = poster_dict[code]
#         cursor.execute(update_sql, (img, code))
#
# conn.commit()



# table join : 영화에 대한 상세정보, json data, 포스터를 모두 확인할 수 있는 테이블 생성
# cursor = conn.cursor()
# cursor.execute("""CREATE TABLE ImdbDB.films_info AS
#                     SELECT A.imdb_code
#                          , A.title
#                          , A.imdb_premiere
#                          , A.imdb_age
#                          , A.imdb_language
#                          , B.json_data
#                          , B.poster_img
#                     FROM ImdbDB.films AS A
#                     LEFT JOIN ImdbDB.imdb_score AS B
#                     ON A.imdb_code = B.imdb_code""")
#
# conn.commit()
#
# cursor.close()
# conn.close()
