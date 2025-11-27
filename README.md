How to run the project (work in progress):
- create locally a virtual environment:
  python -m venv benv
- install the requirements libraries (assuming you are in the parent directory of BackendChatApp):
  pip install -r BackendChatApp\requirements.txt
- run the postgres database container:
  docker compose up -d postgres
- check to see if the container was created:
  docker ps -> you should see postgres:16
- in the CMD with the venv, make alembic migrations:
  alembic upgrade head
- check the existent tables
  docker exec -it chat_db psql -U chat_user -d chat_dev -c "\dt"

If you want to update the database:
- change in the models (create new tables, add new columns)
- then, add in app\db\base.py the import of the class table
- then, run "alembic revision --autogenerate -m "commit message"
- then, run alembic upgrade head
- check in the database if no error occurs
 