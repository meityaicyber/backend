import re

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Optimize thresholdDate filter
old_threshold = r"const thresholdDate = new Date\(now\.getTime\(\) - days \* msPerDay\);\s*vulns = vulns\.filter\(v => new Date\(v\.date\) >= thresholdDate\);"
new_threshold = "const thresholdDate = new Date(now.getTime() - days * msPerDay).toISOString();\n      vulns = vulns.filter(v => v.date >= thresholdDate);"
content = re.sub(old_threshold, new_threshold, content)

# 2. Optimize month parsing
old_month = r"const d = new Date\(v\.date\);\s*const monthStr = \$\{d\.getFullYear\(\)\}-\$\{String\(d\.getMonth\(\) \+ 1\)\.padStart\(2, '0'\)\};"
new_month = "const monthStr = v.date ? v.date.substring(0, 7) : 'Unknown';"
content = re.sub(old_month, new_month, content)

# 3. Optimize sorting
old_sort = r"return vulns\.sort\(\(a, b\) => new Date\(b\.date\) - new Date\(a\.date\)\);"
new_sort = "return vulns.sort((a, b) => a.date < b.date ? 1 : a.date > b.date ? -1 : 0);"
content = re.sub(old_sort, new_sort, content)

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
