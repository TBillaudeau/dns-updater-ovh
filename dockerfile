FROM python:3.8-slim-buster

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

EXPOSE 8501

CMD streamlit run main.py