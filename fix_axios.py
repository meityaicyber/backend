file_path = 'c:/Main Project/Modules/backend/frontend/src/api/axios.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "baseURL: API_URL,",
    "baseURL: API_URL,\n  timeout: 120000, // Default 2 minutes timeout"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
