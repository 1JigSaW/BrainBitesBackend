FROM python:3.8
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "BrainBites.wsgi:application", "--bind", "0.0.0.0:8000", "--log-file", "-"]
