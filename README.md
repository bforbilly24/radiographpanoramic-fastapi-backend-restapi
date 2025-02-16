# src/main.py
Script:
uvicorn src.main:app --reload

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