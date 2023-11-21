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
import re
sys.path.insert(0, './ImdbScores') # mysql 접속정보 저장한 폴더경로 연결
import mysql_connect # mysql 접속정보
import function # function.py - 영화 검색 크롤링
import getInfoImdb # getInfoImdb.py - Imdb 사이트 정보 크롤링
from ImdbScores import re_getInfoImdb

pd.set_option('display.max_columns', 30)
login = mysql_connect.info

# MySQL 서버 연결
conn = pymysql.connect(host = login['host'],
                       port = login['port'],
                       user = login['username'],
                       password = login['password'],
                       db = 'ImdbDB',
                       charset = login['charset'])

data = pd.read_csv('./ImdbScores/data/NetflixOriginals.csv', encoding = "ISO-8859-1")


# ---------------------------------------------------------------------------------------------------------------------------------------------------- #
# TODO-1. Netflix Film에 대한 IMDB 사이트 주소 맵핑
# ex.https://www.imdb.com/title/tt10662450 >> Imdb_code: tt10662450

dict = {}
for index, row in tqdm(data.iterrows(), total=data.shape[0]):

    title = row['Title']
    imdb_url = function.find_imdb_url(title) # 넷플릭스 타이틀을 기준으로 IMDB 사이트 페이지의 url 주소 찾기

    if imdb_url == '':  # url이 안찾아지면 타이틀 전처리해서 다시진행(특수문자 제거)
        re_title = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', '', title)  # 특수문자제거
        re_title = re_title.replace('&', 'and')  # & >> and로 변환

        imdb_url = function.find_imdb_url(re_title)
        dict[index] = imdb_url

    else:
        dict[index] = imdb_url


for key, value in dict.items():
    data.loc[key, 'Imdb_url'] = value # loc을 명시하여 내가 바꾸려는 것이 원본 데이터임을 명확하게 나타낸다.



# TODO-1.2. imdb 사이트 주소를 찾지 못한 대상 case => 해당 Films는 Google에 검색하여 나오는 IMDB 사이트 주소를 찾도록 한다.
"""
case1: 프로그램 명칭이 영어가 아닌 경우 (ex. Òlòt?ré)
case2: 프로그램 명칭이 다르게 표현된 경우 (ex. [netflix] Porta dos Fundos: The First Temptation of Christ > [imdb] The First Temptation of Christ)
case3: 동명의 프로그램이 존재하여 정확한 검색 결과가 안나오는 경우
"""

pass_df = data[data['Imdb_url'].isna()==False].reset_index(drop=True) # imdb_url 찾은 영화
fail_df = data[data['Imdb_url'].isna()].reset_index(drop=True) # imdb_url 찾지 못한 영화 => Google 재검색

dict2 = {}
for index, row in tqdm(fail_df.iterrows(), total=fail_df.shape[0]):

    title = row['Title']
    imdb_url = function.search_google(title)

    if imdb_url == '':  # url이 안찾아지면 타이틀 전처리해서 다시진행(특수문자 제거)
        re_title = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', '', title)  # 특수문자제거
        re_title = re_title.replace('&', 'and')  # & >> and로 변환

        imdb_url = function.search_google(re_title)
        dict2[index] = imdb_url

    else:
        dict2[index] = imdb_url


for key, value in dict2.items():
    fail_df.loc[key, 'Imdb_url'] = value # loc을 명시하여 내가 바꾸려는 것이 원본 데이터임을 명확하게 나타낸다.

netflix_df = pd.concat([pass_df, fail_df], axis = 0, ignore_index = True)

# Imdb_url 전처리
netflix_df['Imdb_url'] = netflix_df['Imdb_url'].apply(getInfoImdb.extract_code)
netflix_df = netflix_df.rename(columns = {'Imdb_url':'Imdb_code'})



# TODO-1.3. 맵핑된 코드 이용해서 IMDB 사이트 세부 정보 추출
imdb_df = netflix_df[['Imdb_code', 'Title']]

for index, row in tqdm(imdb_df.iterrows(), total=imdb_df.shape[0]):
    code = row['Imdb_code']
    elem1, elem2, elem3, genre1, genre2, genre3 = getInfoImdb.find_film_info(code)

    year =  getInfoImdb.find_year(elem1, elem2, elem3)  # 년도정보
    age =  getInfoImdb.find_age(elem1, elem2, elem3)  # 연령정보
    time =  getInfoImdb.find_time(elem1, elem2, elem3)  # 시간정보

    imdb_df.loc[index, 'Imdb_Premiere'] = year
    imdb_df.loc[index, 'Imdb_Age'] = age
    imdb_df.loc[index, 'Imdb_Time'] = time

    imdb_df.loc[index, 'Imdb_Genre1'] = genre1
    imdb_df.loc[index, 'Imdb_Genre2'] = genre2
    imdb_df.loc[index, 'Imdb_Genre3'] = genre3



# ---------------------------------------------------------------------------------------------------------------------------------------------------- #
# TODO-2. 동일 프로그램인지 확인(Netflix, Imdb 사이트 정보 비교)
merge_df = netflix_df.merge(imdb_df, on = 'Imdb_code')
merge_df = merge_df[['Title_x', 'Genre', 'Premiere', 'Runtime', 'IMDB Score', 'Language', 'Imdb_code', 'Imdb_Premiere', 'Imdb_Age', 'Imdb_Time', 'Imdb_Genre1', 'Imdb_Genre2', 'Imdb_Genre3']]
merge_df = merge_df.rename(columns = {'Title_x':'Title'})

merge_df['Year_check'] = ''
merge_df['Genre_check'] = ''

for index, row in tqdm(merge_df.iterrows(), total=merge_df.shape[0]): # 맵핑된 Id 기준으로 Netflix 원본 데이터와 IMDB 사이트에서 추출한 정보를 비교한다.
    nflx_year = row['Premiere'][-4:]
    nflx_genre = row['Genre']
    imdb_code = row['Imdb_code']
    imdb_year = row['Imdb_Premiere']
    imdb_genre = [row['Imdb_Genre1'], row['Imdb_Genre2'], row['Imdb_Genre3']]

    try:
        # 년도비교
        if nflx_year == imdb_year:
            merge_df.loc[index, 'Year_check'] = 'Y'

        else:
            merge_df.loc[index, 'Year_check'] = 'N'

        # 장르비교
        if nflx_genre in imdb_genre:
            merge_df.loc[index, 'Genre_check'] = 'Y'

        else:
            merge_df.loc[index, 'Genre_check'] = 'N'

    except:
        merge_df.loc[index, 'Year_check'] = 'N'
        merge_df.loc[index, 'Genre_check'] = 'N'

pass_df2 = merge_df[(merge_df['Year_check']=='Y')&(merge_df['Genre_check']=='Y')].reset_index(drop=True) # 년도, 장르 모두 일치하는 경우
fail_df2 = merge_df[(merge_df['Year_check']=='N')|(merge_df['Genre_check']=='N')].reset_index(drop=True) # 년도 or 장르 중 하나가 일치하지 않은 경우



# TODO-2.1. Netflix, Imdb 사이트 정보가 다른 프로그램 재검색
"""
case1. Year(N), Genre(Y) : IMDB 사이트에서 프로그램 재검색
case2. Year(N), Genre(N) : IMDB 사이트에서 프로그램 재검색
case3. Year(Y), Genre(N) : 장르 표현에 대한 전처리 필요
"""

fail_year_df = fail_df2[(fail_df2['Year_check']=='N')].reset_index(drop=True) # case1,2: 프로그램 재검색
fail_genre_df = fail_df2[(fail_df2['Year_check']=='Y')&(fail_df2['Genre_check']=='N')].reset_index(drop=True) # case3: 장르표현처리



# TODO-2.1.1. 프로그램 재검색
fail_year_df = fail_year_df[['Title', 'Genre', 'Premiere', 'Runtime', 'IMDB Score', 'Language']]

dict3 = {}
for index, row in tqdm(fail_year_df.iterrows(), total=fail_year_df.shape[0]):
    nflx_title = row['Title']
    nflx_year = row['Premiere'][-4:]

    imdb_url = re_getInfoImdb.refind_imdb_url(nflx_title, nflx_year) # 'https://www.imdb.com/find/?q=' + title + '&s=tt&exact=true
    imdb_code = getInfoImdb.extract_code(imdb_url)

    if imdb_code == '':  # 특수문자 제거하고 재검색
        nflx_title = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', '', nflx_title)
        imdb_url = re_getInfoImdb.refind_imdb_url(nflx_title, nflx_year)
        imdb_code = getInfoImdb.extract_code(imdb_url)

    if imdb_code == '': # url 주소 수정해서 사이트 재검색
        imdb_url = re_getInfoImdb.refind_imdb_url_noexact(nflx_title, nflx_year) # 'https://www.imdb.com/find/?q=' + title
        imdb_code = getInfoImdb.extract_code(imdb_url)

    if imdb_code == '':  # url 주소 수정해서 사이트 재검색(특수문자 제거)
        nflx_title = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', '', nflx_title)
        imdb_url = re_getInfoImdb.refind_imdb_url_noexact(nflx_title, nflx_year)
        imdb_code = getInfoImdb.extract_code(imdb_url)

    dict3[index] = imdb_code

fail_year_df_copy = fail_year_df.copy() # 원본복사본 저장

for key, value in dict3.items():
    fail_year_df.loc[key, 'Imdb_code'] = value



# TODO-2.1.2. 재검색 후에도 기준이 명확하지 않은 경우(동일 프로그램에 대해 사이트별로 년도가 다르게 기재된 경우) => 수기 맵핑 진행
# fail_info : 동일 프로그램에 대해 사이트별로 정보가 다르게 기재된 것으로 이 부분은 수기 맵핑하여 Pass
fail_info = ['Dolly Kitty and Those Twinkling Stars', 'Lionheart', 'The Polka King', 'Roxanne Roxanne', 'Cargo',
             'The Legend of Cocaine Island', 'Isi & Ossi', 'Tramps', 'Milestone', 'Hope Frozen: A Quest to Live Twice',
             'Imperial Dreams', 'Little Miss Sumo', 'Night in Paradise', 'A Love Song for Latasha', 'Long Live Brij Mohan',
             'Spelling the Dream', "ReMastered: The Lion's Share", "Angela's Christmas", 'El Pepe: A Supreme Life',
             'My Beautiful Broken Brain', 'Soni', 'Sitara: Let Girls Dream', 'The Other One: The Long Strange Trip of Bob Weir', 'Òlòt?ré']

fail_year_df.loc[16, 'Imdb_code'] = 'tt9176296'
fail_year_df.loc[22, 'Imdb_code'] = 'tt7707314'
fail_year_df.loc[32, 'Imdb_code'] = 'tt5539052'
fail_year_df.loc[36, 'Imdb_code'] = 'tt5796838'
fail_year_df.loc[37, 'Imdb_code'] = 'tt3860916'
fail_year_df.loc[40, 'Imdb_code'] = 'tt8106596'
fail_year_df.loc[42, 'Imdb_code'] = 'tt9806322'
fail_year_df.loc[45, 'Imdb_code'] = 'tt4991512'
fail_year_df.loc[49, 'Imdb_code'] = 'tt12779208'
fail_year_df.loc[50, 'Imdb_code'] = 'tt8060472'
fail_year_df.loc[51, 'Imdb_code'] = 'tt3331028'
fail_year_df.loc[52, 'Imdb_code'] = 'tt9195844'
fail_year_df.loc[54, 'Imdb_code'] = 'tt12792418'
fail_year_df.loc[55, 'Imdb_code'] = 'tt8993180'
fail_year_df.loc[56, 'Imdb_code'] = 'tt6514010'
fail_year_df.loc[59, 'Imdb_code'] = 'tt6193522'
fail_year_df.loc[60, 'Imdb_code'] = 'tt9046576'
fail_year_df.loc[61, 'Imdb_code'] = 'tt7829544'
fail_year_df.loc[63, 'Imdb_code'] = 'tt8900434'
fail_year_df.loc[66, 'Imdb_code'] = 'tt3815136'
fail_year_df.loc[73, 'Imdb_code'] = 'tt6078866'
fail_year_df.loc[76, 'Imdb_code'] = 'tt11064862'
fail_year_df.loc[77, 'Imdb_code'] = 'tt3692768'
fail_year_df.loc[84, 'Imdb_code'] = 'tt9725830'



# TODO-2.1.3. 새로 맵핑된 Imdb 코드 기준으로 Imdb 사이트 세부 정보 추출
# Imdb 사이트 상세정보 수집
for index, row in tqdm(fail_year_df.iterrows(), total=fail_year_df.shape[0]):
    code = row['Imdb_code']
    elem1, elem2, elem3, genre1, genre2, genre3 = getInfoImdb.find_film_info(code)

    year = getInfoImdb.find_year(elem1, elem2, elem3)  # 년도정보
    age = getInfoImdb.find_age(elem1, elem2, elem3)  # 연령정보
    time = getInfoImdb.find_time(elem1, elem2, elem3)  # 시간정보

    fail_year_df.loc[index, 'Imdb_Premiere'] = year
    fail_year_df.loc[index, 'Imdb_Age'] = age
    fail_year_df.loc[index, 'Imdb_Time'] = time

    fail_year_df.loc[index, 'Imdb_Genre1'] = genre1
    fail_year_df.loc[index, 'Imdb_Genre2'] = genre2
    fail_year_df.loc[index, 'Imdb_Genre3'] = genre3


# 새로 맵핑된 Imdb 코드 기준으로 Netflix 원본 데이터와 IMDB 사이트에서 추출한 정보를 비교한다.
for index, row in tqdm(fail_year_df.iterrows(), total=fail_year_df.shape[0]):
    nflx_year = row['Premiere'][-4:]
    nflx_genre = row['Genre']
    imdb_code = row['Imdb_code']
    imdb_year = row['Imdb_Premiere']
    imdb_genre = [row['Imdb_Genre1'], row['Imdb_Genre2'], row['Imdb_Genre3']]

    try:
        # 년도비교
        if nflx_year == imdb_year:
            fail_year_df.loc[index, 'Year_check'] = 'Y'

        else:
            fail_year_df.loc[index, 'Year_check'] = 'N'

        # 장르비교
        if nflx_genre in imdb_genre:
            fail_year_df.loc[index, 'Genre_check'] = 'Y'

        else:
            fail_year_df.loc[index, 'Genre_check'] = 'N'

    except:
        fail_year_df.loc[index, 'Year_check'] = 'N'
        fail_year_df.loc[index, 'Genre_check'] = 'N'


# (위에서 찾은 fail_info를 제외하고) 년도 정보가 일치하지 않은 부분 확인
for index, row in fail_year_df.iterrows():
    check = row['Year_check']
    title = row['Title']

    if check == 'Y':
        pass

    elif check == 'N' and title in fail_info:
        pass

    else:
        print(index, title)


# 동명의 프로그램이 있어서 잘못 맵핑된 부분 => 수정완료
fail_year_df.loc[[20, 46, 68, 74, 79, 81]]
fail_year_df.loc[20, 'Imdb_code'] = 'tt2338454'
fail_year_df.loc[46, 'Imdb_code'] = 'tt11644096'
fail_year_df.loc[68, 'Imdb_code'] = 'tt11161474'
fail_year_df.loc[74, 'Imdb_code'] = 'tt11423784'
fail_year_df.loc[79, 'Imdb_code'] = 'tt6939026'
fail_year_df.loc[81, 'Imdb_code'] = 'tt11318624'

for index, row in tqdm(fail_year_df.iterrows(), total=fail_year_df.shape[0]): # 사이트 정보 재수집

    if index in [20, 46, 68, 74, 79, 81]: # 동명 프로그램에 대해 수정한 부분만 다시 사이트 정보 재수집
        code = row['Imdb_code']
        elem1, elem2, elem3, genre1, genre2, genre3 = getInfoImdb.find_film_info(code)

        year = getInfoImdb.find_year(elem1, elem2, elem3)  # 년도정보
        age = getInfoImdb.find_age(elem1, elem2, elem3)  # 연령정보
        time = getInfoImdb.find_time(elem1, elem2, elem3)  # 시간정보

        fail_year_df.loc[index, 'Imdb_Premiere'] = year
        fail_year_df.loc[index, 'Imdb_Age'] = age
        fail_year_df.loc[index, 'Imdb_Time'] = time

        fail_year_df.loc[index, 'Imdb_Genre1'] = genre1
        fail_year_df.loc[index, 'Imdb_Genre2'] = genre2
        fail_year_df.loc[index, 'Imdb_Genre3'] = genre3



# TODO-2.1.4. 년도기준 재맵핑 완료
"""
최종적으로 확인해본 결과 아래 두 경우의 예외를 제외하고는 모두 올바르게 년도 맵핑이 완료되었음을 확인했다.
아래의 두 경우에 대해서는 Imdb_code를 수기 맵핑 진행하였다.

case1: 사이트 자체에서 년도 정보를 잘못 입력한 경우(fail_info 리스트)
case2: 년도 설명이 조금 다르게 나와있어서 맵핑을 못한경우(ex. Episode aired Mar 20, 2019)
"""



# TODO-2.2. Netflix, Imdb 사이트의 장르가 서로 다르게 표현된 경우
merge_df2 = pd.concat([fail_year_df, fail_genre_df])
merge_df2 = merge_df2.fillna('')


# TODO-2-2-1. 장르 단어 전처리
for index, row in tqdm(merge_df2.iterrows(), total=merge_df2.shape[0]):
    genres = row['Genre']  # netflix genre

    # '/' 특수문자 기준으로 split
    if '/' in genres:  # ex.Musical/Western/Fantasy
        genres = genres.split('/')
        genres = list(map(lambda x: x.strip(), genres))  # 공백제거

    else:
        genres = [genres]

    # 단어 내에서 띄어쓰기 기준으로 split
    for genre in genres:
        new_genre = genre.split(' ')
        genres.remove(genre)
        genres += new_genre

    new_genre1 = genres[0] if 0 < len(genres) else ''
    new_genre2 = genres[1] if 1 < len(genres) else ''
    new_genre3 = genres[2] if 2 < len(genres) else ''
    new_genre4 = genres[3] if 3 < len(genres) else ''

    merge_df2.loc[index, 'Nflx_Genre1'] = new_genre1
    merge_df2.loc[index, 'Nflx_Genre2'] = new_genre2
    merge_df2.loc[index, 'Nflx_Genre3'] = new_genre3
    merge_df2.loc[index, 'Nflx_Genre4'] = new_genre4

merge_df2 = merge_df2[['Title', 'Nflx_Genre1', 'Nflx_Genre2', 'Nflx_Genre3', 'Nflx_Genre4', 'Premiere', 'Runtime', 'IMDB Score', 'Language', 'Imdb_code', 'Imdb_Premiere', 'Imdb_Age', 'Imdb_Time', 'Imdb_Genre1', 'Imdb_Genre2', 'Imdb_Genre3', 'Year_check', 'Genre_check']]

# netflix genre 소문자 변환
merge_df2['Nflx_Genre1'] = merge_df2['Nflx_Genre1'].str.lower()
merge_df2['Nflx_Genre2'] = merge_df2['Nflx_Genre2'].str.lower()
merge_df2['Nflx_Genre3'] = merge_df2['Nflx_Genre3'].str.lower()
merge_df2['Nflx_Genre4'] = merge_df2['Nflx_Genre4'].str.lower()

# imdb genre 소문자 변환
merge_df2['Imdb_Genre1'] = merge_df2['Imdb_Genre1'].str.lower()
merge_df2['Imdb_Genre2'] = merge_df2['Imdb_Genre2'].str.lower()
merge_df2['Imdb_Genre3'] = merge_df2['Imdb_Genre3'].str.lower()

merge_df2 = merge_df2.drop(['Genre_check'], axis='columns')



# TODO-2-2-2. 사이트별 장르 비교
for index, row in tqdm(merge_df2.iterrows(), total=merge_df2.shape[0]):
    nflx_genre = [row['Nflx_Genre1'], row['Nflx_Genre2'], row['Nflx_Genre3'], row['Nflx_Genre4']]
    imdb_genre = [row['Imdb_Genre1'], row['Imdb_Genre2'], row['Imdb_Genre3']]
    check = 'N'

    try:
        # 장르비교

        for n_genre in nflx_genre:
            if n_genre in imdb_genre:
                check = 'Y'
                merge_df2.loc[index, 'Genre_check'] = check
                break

    except:
        merge_df2.loc[index, 'Genre_check'] = check

pass_genre_df = merge_df2[merge_df2['Genre_check']=='Y'].reset_index(drop=True) # 장르가 올바르게 맵핑된 경우
fail_genre_df = merge_df2[merge_df2['Genre_check']=='N'].reset_index(drop=True) # 장르가 다르게 맵핑된 경우(없음을 확인)



# TODO-2-2-3. 장르기준 재맵핑 완료
merge_df2 = merge_df2[merge_df2['Genre_check'].isna()==False]
result_df = merge_df2



# ---------------------------------------------------------------------------------------------------------------------------------------------------- #
# TODO-3. result_df > insert Mysql
cursor = conn.cursor() # MySQL 서버와 연결할 수 있는 cursor 생성

result_df = result_df[['Imdb_code', 'Title', 'Imdb_Premiere', 'Imdb_Age', 'Imdb_Time', 'IMDB Score', 'Language', 'Nflx_Genre1', 'Nflx_Genre2', 'Nflx_Genre3', 'Nflx_Genre4']] # 컬럼 순서 변경
result_df = result_df.replace({np.nan: None})

sql = """INSERT INTO ImdbDB.films (imdb_code, title, imdb_premiere, imdb_age, imdb_time, imdb_score, imdb_language, nflx_genre1, nflx_genre2, nflx_genre3, nflx_genre4) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""


for index, row in result_df.iterrows():
    cursor.execute(sql, tuple(row))

conn.commit()

cursor.close() # cursor 닫기
conn.close() # db connection 닫기



# ---------------------------------------------------------------------------------------------------------------------------------------------------- #
# TODO-4. Imdb 사이트 나라별 평가점수, 포스터 이미지 수집
country_dict = {}  # (key: imdb_code, value: imdb site's json)
poster_dict = {} # (key: imdb_code, value: poster img)
error = list()

for index, row in tqdm(result_df.iterrows(), total = result_df.shape[0]):

    code = row['Imdb_code']
    url = 'https://www.imdb.com/title/' + code + '/ratings/' # 평점 제공 사이트
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


# TODO-4-2. Imdb 사이트 나라별 평가점수, 포스터 이미지 수집 > insert Mysql
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



# ---------------------------------------------------------------------------------------------------------------------------------------------------- #
# TODO-5. 영화에 대해 수집한 모든 정보를 가지는 Main 테이블 생성 > Flask를 연동해서 웹페이지 보여줄 때 사용할 테이블
cursor = conn.cursor()

# JOIN - 영화정보, Json data, 포스터이미지
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

