FROM python:latest
WORKDIR /BlogApp

COPY app.py .
COPY templates templates/
COPY static static/
COPY requirments.txt .
RUN pip install -r /BlogApp/requirments.txt
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "4000"]
