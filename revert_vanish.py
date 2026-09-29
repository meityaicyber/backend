import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Change "Customize Widgets" to "Unlock Widgets"
    content = content.replace('Customize Widgets', 'Unlock Widgets')
    
    # 2. Revert the conditional rendering so widgets always render
    pattern = r'\{visibleWidgets\.includes\("([^"]+)"\) && \(\s*(<div key="\1">[\s\S]*?</div>)\s*\)\}'
    def repl(m):
        return m.group(2)
    content = re.sub(pattern, repl, content)

    # 3. Apply the static mapping to the layouts prop
    layout_prop_search = r'layouts=\{layouts\}'
    layout_prop_replace = '''layouts={Object.keys(layouts).reduce((acc, key) => ({
          ...acc,
          [key]: layouts[key].map(l => ({ ...l, static: !visibleWidgets.includes(l.i) }))
        }), {})}'''
    
    content = content.replace(layout_prop_search, layout_prop_replace)
    
    # Add visual feedback for locked widgets (e.g. change cursor if not unlocked)
    # We can just change draggableHandle to a specific class that is only present when unlocked?
    # RGL's static property automatically adds a class and disables drag/resize, which is sufficient.

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {file_path}")

fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx')
fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx')

