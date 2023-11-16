from flask import Flask, render_template, request
import pymysql
import sys
import json
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
    sql = f"""SELECT imdb_code, title, imdb_premiere, imdb_age, imdb_language, json_data, poster_img
                FROM ImdbDB.films_info
                WHERE imdb_code = '{imdb_code}'"""

    cursor.execute(sql)
    film_data = cursor.fetchall()

    return film_data

def visualize_barChart(data):

    import matplotlib
    matplotlib.use('Agg') # non-interactive backend
    import matplotlib.pyplot as plt

    id = data[0][0]
    json_data = json.loads(data[0][5])

    countries = [j['displayText'] for j in json_data]
    rates = [j['aggregateRating'] for j in json_data]
    avg_rate = sum(rates) / len(rates)  # ratings 평균

    plt.figure(figsize=(10, 8))
    plt.bar(countries, rates, label='rating',
                color=['darkslategray', 'darkcyan', 'cadetblue', 'powderblue', 'paleturquoise'])
    plt.xlabel('Country', labelpad=10, fontdict={'fontweight': 'bold', 'size': 13})  # x축 레이블(labelpad: 여백지정)
    plt.ylabel('Rating', labelpad=15, fontdict={'fontweight': 'bold', 'size': 13})  # y축 레이블
    plt.ylim([0, 10])  # y축범위
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.title('Imdb Ratings by Country', pad=10, fontdict={'fontweight': 'bold', 'size': 20})  # 타이틀(pad: 그래프와의 간격)
    plt.legend(fontsize=13, loc='upper right')  # 범례위치, 폰트크기 설정

    # 그래프에 평점 value 표시하기
    for i in range(len(countries)):
        plt.text(countries[i], rates[i], rates[i], ha='center', va='bottom', size=13)  # plt.text(x,y,z) -> (x,y)위치에 z값표시

    plt.axhline(y=avg_rate, color='darkgrey', linestyle='--', label='Average Rating')  # 평균값을 수평선으로 표시
    plt.legend(fontsize=13)

    # 참고. 프로젝트 폴더에 static directory가 만들어져 있어야 한다.
    # static directory -> Flask가 해당 디렉터리에 있는 정적인 파일을 찾아서 Client에게 제공한다.
    image = 'static/rate_chart.png'
    plt.savefig(image)

    return image


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
    chart_image = visualize_barChart(film)

    return render_template('film_detail.html', film = film, chart_image = chart_image)


# flask 실행 (cd 파이썬코드경로 > python3 ~.py)
# flask 실행 오류나면 (lsof -i :5000 > kill -9 <PID>)
if __name__ == '__main__':
    app.run(debug=True)
