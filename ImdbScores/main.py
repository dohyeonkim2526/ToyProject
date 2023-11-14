import pandas as pd
import numpy as np
import pymysql
import sys
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

# cursor 닫기
cursor.close()
# db connection 닫기
conn.close()



