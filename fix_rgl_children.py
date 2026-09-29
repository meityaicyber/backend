import re

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to find patterns like:
    # <div key="some_id">
    #   {visibleWidgets.includes("some_id") && (
    #      <Card>...</Card>
    #   )}
    # </div>
    #
    # And replace with:
    # {visibleWidgets.includes("some_id") && (
    #   <div key="some_id">
    #     <Card>...</Card>
    #   </div>
    # )}
    
    # Let's use regex.
    pattern = r'(<div key="([^"]+)">\s*)\{visibleWidgets\.includes\("\2"\) && \(\s*(<ChartCard[\s\S]*?</ChartCard>)\s*\)\}\s*</div>'
    
    def repl(m):
        w_id = m.group(2)
        inner_card = m.group(3)
        return f'{{visibleWidgets.includes("{w_id}") && (\n          <div key="{w_id}">\n            {inner_card}\n          </div>\n        )}}'

    new_content = re.sub(pattern, repl, content)
    
    # For ML page, it uses <Card ... instead of <ChartCard
    pattern2 = r'(<div key="([^"]+)">\s*)\{visibleWidgets\.includes\("\2"\) && \(\s*(<Card[\s\S]*?</Card>)\s*\)\}\s*</div>'
    def repl2(m):
        w_id = m.group(2)
        inner_card = m.group(3)
        return f'{{visibleWidgets.includes("{w_id}") && (\n          <div key="{w_id}">\n            {inner_card}\n          </div>\n        )}}'

    new_content = re.sub(pattern2, repl2, new_content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed {file_path}")

fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx')
fix_file(r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx')

