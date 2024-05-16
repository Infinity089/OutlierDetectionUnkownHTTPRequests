FROM python:3.8

WORKDIR /app

COPY app /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
ENV FLASK_APP=log_collector.py
CMD ["flask", "run", "--host", "0.0.0.0"]