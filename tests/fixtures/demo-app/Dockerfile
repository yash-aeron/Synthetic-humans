FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn jinja2

COPY tests/fixtures/demo_app/ /app/demo_app/

EXPOSE 5050

CMD ["uvicorn", "demo_app.server:app", "--host", "0.0.0.0", "--port", "5050"]
