### About Project
넷플릭스 영화에 대해 IMDB 사이트에서의 나라별 평점을 시각화하는 프로젝트

IMDB 사이트의 평점이 계속 업데이트된다는 것을 이용하여 보고 싶은 영화에 대해 **나라별 최신 평점**을 확인하고자 한다. 이때, 영화를 구분하는 기준은 IMDB 사이트 주소에 있는 고유 코드값을 기준으로 한다.


사용 데이터셋: Kaggle [Netflix Original Films & IMDB Scores]
https://www.kaggle.com/datasets/luiscorter/netflix-original-films-imdb-scores

##
#### [2023.09 ~ 2023.11] 넷플릭스 영화 제목을 가지고 IMDB 사이트의 코드값 맵핑
* 과제1 - 영화명이 영문이 아니거나 특수문자가 포함된 경우에 대해 전처리
  * 해결 - Google에 검색해서 나오는 IMDB 영화 서칭
  

* 과제2 - 영화 명칭이 사이트별로 서로 다르게 표현된 경우에 대해 전처리 (ex. Netflix(Porta dos Fundos: The First Temptation of Christ) <-> Imdb(The First Temptation of Christ))
  * 해결 - 영화 세부정보(ex. 개봉년도, 장르)를 이용해서 동일한 영화인지 비교
  

* 과제3 - 동명의 영화가 존재하여 정확한 검색 결과가 안나오는 경우에 대해 전처리
  * 해결 - 영화 세부정보(ex. 개봉년도, 장르)를 이용해서 동일한 영화인지 비교
  

* 과제4 - 장르에 대해 서로 다르게 표현한 부분에 대해 전처리
  * 해결 - 영화에 대해 사이트별 장르를 list로 처리하여 장르가 겹치는지 확인



## 
#### [2023.11 ~] 맵핑이 완료되어 맵핑된 코드값을 가지고 IMDB 사이트의 나라별 평점을 수집하고 시각화 진행(with Flask)
* 과제1 - Flask 시각화 진행 (ImdbDB.imdb_score.imdb 코드값을 가지고 영화 정보 테이블의 데이터를 가져와서 '영화정보+포스터+나라별 평점' 시각화해보기)
* 과제2 - 코드값 매핑을 위해 작성한 코드 리팩터링
