venv:
using python
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
or if using python3
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

Setup Database:
### Open alembic.ini and adjust sqlalchemy.url to match the PostgreSQL/MySQL database
_sqlalchemy.url = postgresql://dbusername:dbpassword@localhost:5432/yourdatabase_
or
_sqlalchemy.url = mysql+pymysql://dbusername:dbpassword@localhost:3306/yourdatabase_

Migrate:
### make migration
```bash
alembic revision --autogenerate -m "name_your_table"
```

### if there are changes in the SQLAlchemy model (e.g. adding new columns, changing data types, or adding tables), you need to perform a new migration and run the upgrade.
```bash
alembic revision --autogenerate -m "add column phone into users"
```
This will create a new migration file in migrations/versions/ with the format
_migrations/versions/xxxxxxxxxxxx_add_phone_column.py_

```bash
alembic upgrade head
```

alembic command:
### init alembic
```bash
alembic init migrations
```

### showing history
```bash
alembic history
```

### see a list of all commits (revision IDs) that have been made in the folder
```bash
alembic history --verbose
```

### view migration status in database
```bash
alembic current
```

### see if there are any migrations that have not been applied
```bash
alembic heads
```

### rollback
```bash
alembic downgrade -1
```
or by id
```bash
alembic downgrade <commit_id>
```

### rollback
```bash
alembic heads
```

Compile :
### src/main.py
```bash
uvicorn src.main:app --reload
```

# Folder Structure

```
└── 📁migrations
    └── 📁versions
        └── 951cd5d7639e_initial_migration.py
        └── abb10ccaa8b5_add_tokenblacklist_table.py
        └── cc893fd61fb5_add_expires_at_to_token_blacklist.py
        └── e4eb2e45db20_initial_migration.py
    └── env.py
    └── README
    └── script.py.make
└── 📁src
    └── 📁app
        └── 📁v1
            └── api.py
            └── 📁endpoints
                └── auth.py
                └── category.py
                └── radiograph.py
    └── 📁core
        └── config.py
        └── security.py
    └── 📁db
        └── base.py
        └── session.py
    └── 📁handlers
        └── response_handler.py
    └── 📁ml_models
        └── unet_gigi_100.h5
        └── unet_gigi_penyakit.h5
    └── 📁models
        └── category_model.py
        └── radiograph_model.py
        └── token_blacklist_model.py
        └── user_model.py
    └── 📁schemas
        └── category_schema.py
        └── radiograph_schema.py
        └── user_schema.py
    └── 📁seeds
        └── category_seeder.py
        └── run_seeder.py
        └── user_seeder.py
    └── 📁services
        └── radiograph_service.py
    └── 📁utils
        └── dependencies.py
    └── .DS_Store
    └── main.py
```