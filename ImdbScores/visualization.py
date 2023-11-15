from flask import Flask, render_template, request
import pymysql
import sys
sys.path.insert(0, './ImdbScores') # mysql 접속정보 저장한 폴더경로 연결
import mysql_connect # mysql 접속정보

app = Flask(__name__)
login = mysql_connect.info

# MySQL 서버 연결
conn = pymysql.connect(host = login['host'],
                       port = login['port'],
                       user = login['username'],
                       password = login['password'],
                       db = 'ImdbDB',
                       charset=login['charset'])


# 영화 리스트를 10개씩 확인하기 위해 function 정의
def fetch_films(page_number):
    cursor = conn.cursor() # 데이터 접근

    limit = 10
    offset = (page_number-1) * limit
    sql = f"""SELECT imdb_code, title, imdb_premiere, imdb_age, imdb_time, imdb_language, imdb_score, nflx_genre1, nflx_genre2, nflx_genre3, nflx_genre4
                FROM ImdbDB.films
                ORDER BY imdb_score DESC
                LIMIT {limit} OFFSET {offset}"""

    cursor.execute(sql) # sql query 실행
    film_data = cursor.fetchall() # 실행결과 데이터 가져오기

    return film_data

def fetch_films_detail(imdb_code):
    cursor = conn.cursor()
    sql = f"""SELECT imdb_code, json_data, poster_img
                FROM ImdbDB.imdb_score
                WHERE imdb_code = '{imdb_code}'"""

    cursor.execute(sql)
    film_data = cursor.fetchall()

    return film_data

@app.route('/') # 메인화면
def film_info():
    # page number
    page_number = int(request.args.get('page', 1))

    # film info with page
    films = fetch_films(page_number)

    # 참고.html 파일은 하위 templates 폴더 아래에 존재해야 한다.
    return render_template('films_info.html', films = films, page_number = page_number)


@app.route('/film/<imdb_code>') # 영화 상세화면
def show_film(imdb_code):
    film = fetch_films_detail(imdb_code)

    return render_template('film_detail.html', film = film)


# flask 실행 (cd 파이썬코드경로 > python3 ~.py)
# flask 실행 오류나면 (lsof -i :5000 > kill -9 <PID>)
if __name__ == '__main__':
    app.run(debug=True)
