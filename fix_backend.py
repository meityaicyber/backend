import re

# 1. Fix database.py
db_file = 'c:/Main Project/Modules/backend/backend/app/database.py'
with open(db_file, 'r', encoding='utf-8') as f:
    db_content = f.read()

db_content = db_content.replace(
    "poolclass=NullPool,",
    "pool_size=20,\n    max_overflow=20,"
)
with open(db_file, 'w', encoding='utf-8') as f:
    f.write(db_content)

# 2. Fix config.py
config_file = 'c:/Main Project/Modules/backend/backend/app/config.py'
with open(config_file, 'r', encoding='utf-8') as f:
    config_content = f.read()

config_content = config_content.replace(
    "MAX_FILE_SIZE_MB: int = 50",
    "MAX_FILE_SIZE_MB: int = 100"
)
with open(config_file, 'w', encoding='utf-8') as f:
    f.write(config_content)

# 3. Fix pipeline.py
pipeline_file = 'c:/Main Project/Modules/backend/backend/app/routers/pipeline.py'
with open(pipeline_file, 'r', encoding='utf-8') as f:
    pipeline_content = f.read()

pipeline_content = pipeline_content.replace(
    "timeout=60.0",
    "timeout=180.0"
)
with open(pipeline_file, 'w', encoding='utf-8') as f:
    f.write(pipeline_content)

# 4. Fix nginx.conf
nginx_file = 'c:/Main Project/Modules/backend/frontend/nginx.conf'
with open(nginx_file, 'r', encoding='utf-8') as f:
    nginx_content = f.read()

nginx_content = nginx_content.replace(
    "client_max_body_size 50M;",
    "client_max_body_size 100M;"
)
nginx_content = nginx_content.replace(
    "proxy_read_timeout 120s;",
    "proxy_read_timeout 300s;\n        proxy_connect_timeout 10s;\n        proxy_send_timeout 120s;"
)
with open(nginx_file, 'w', encoding='utf-8') as f:
    f.write(nginx_content)

print('Backend fixes applied successfully.')
