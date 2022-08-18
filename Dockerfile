# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./app /code/app

ENV PORT 8080

# 
#$CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
