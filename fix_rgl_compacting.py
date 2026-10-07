import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to replace:
    # static: !visibleWidgets.includes(l.i)
    # with:
    # isDraggable: visibleWidgets.includes(l.i), isResizable: visibleWidgets.includes(l.i)
    
    # Let's search and replace
    search_str = "static: !visibleWidgets.includes(l.i)"
    replace_str = "isDraggable: visibleWidgets.includes(l.i), isResizable: visibleWidgets.includes(l.i)"
    
    if search_str in content:
        content = content.replace(search_str, replace_str)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")
    else:
        print(f"String not found in {file_path}")

fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx')
fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx')

