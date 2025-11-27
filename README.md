python -m venv .venv
.venv\Scripts\activate           # pe Windows
pip install -r requirements.txt

docker compose up -d postgres

alembic upgrade head

docker exec -it chat_db psql -U chat_user -d chat_dev -c "\dt"           # to verify the tables

