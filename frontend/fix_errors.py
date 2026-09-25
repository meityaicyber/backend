import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/contexts/BulkUploadContext.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_error_parse = "const msg = err.response?.data?.detail || err.message || 'Operation Failed';"

new_error_parse = """let msg = 'Operation failed';
        if (err.response) {
          if (err.response.data && typeof err.response.data.detail === 'string') {
            msg = err.response.data.detail;
          } else if (err.response.data && Array.isArray(err.response.data.detail)) {
            msg = err.response.data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else if (err.response.status === 413) {
            msg = "File size limit exceeded";
          } else if (err.response.status === 500) {
             // If there's a specific message in the response text, try to use it
             if (typeof err.response.data === 'string' && err.response.data.length < 200 && !err.response.data.includes('<html')) {
                msg = err.response.data;
             } else {
                msg = "Internal server error on backend";
             }
          } else {
            msg = `Request failed with status code ${err.response.status}`;
          }
        } else {
          msg = err.message || 'Network error';
        }"""

content = content.replace(old_error_parse, new_error_parse)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

file_path2 = 'c:/Main Project/Modules/backend/frontend/src/pages/UploadReportPage.jsx'
with open(file_path2, 'r', encoding='utf-8') as f:
    content2 = f.read()

# In UploadReportPage there are multiple places:
# const msg = err.response?.data?.detail || 'Operation failed';
# const msg = err.response?.data?.detail;

new_err_block = """let msg = 'Operation failed';
          if (err.response) {
            if (err.response.data && typeof err.response.data.detail === 'string') {
              msg = err.response.data.detail;
            } else if (err.response.data && Array.isArray(err.response.data.detail)) {
              msg = err.response.data.detail.map(d => d.msg).join(', ');
            } else if (err.response.status === 413) {
              msg = "File size limit exceeded";
            } else if (err.response.status === 500) {
              msg = "Internal server error on backend";
            } else {
              msg = `Request failed with status code ${err.response.status}`;
            }
          } else {
            msg = err.message || 'Network error';
          }"""

content2 = re.sub(r"const msg = err\.response\?\.data\?\.detail \|\| 'Operation failed';", new_err_block, content2)

content2 = re.sub(r"const msg = err\.response\?\.data\?\.detail;", new_err_block, content2)

with open(file_path2, 'w', encoding='utf-8') as f:
    f.write(content2)

print('Done!')
