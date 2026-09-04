FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
COPY offline_packages/python ./offline_packages/python
RUN pip install --no-index --find-links=./offline_packages/python -r backend/requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
