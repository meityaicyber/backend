import re

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix filteredVulnerabilities dependencies
old_dep1 = r"\}, \[viewMode, selectedAgencyId, selectedFileId, timeRange, selectedSeverities, selectedStatuses\]\);"
new_dep1 = "}, [allVulnerabilities, viewMode, selectedAgencyId, selectedFileId, timeRange, selectedSeverities, selectedStatuses]);"
content = re.sub(old_dep1, new_dep1, content)

# 2. Fix aggregatedData dependencies
old_dep2 = r"\}, \[filteredVulnerabilities, viewMode, selectedAgencyId, selectedFileId\]\);"
new_dep2 = "}, [filteredVulnerabilities, files, viewMode, selectedAgencyId, selectedFileId]);"
content = re.sub(old_dep2, new_dep2, content)

# 3. Fix month parsing in aggregatedData (since regex failed)
old_month = "const d = new Date(v.date);\n      const monthStr = ${d.getFullYear()}-;"
new_month = "const monthStr = v.date ? v.date.substring(0, 7) : 'Unknown';"
content = content.replace(old_month, new_month)

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
