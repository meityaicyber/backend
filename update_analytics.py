import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add imports
if 'react-grid-layout' not in content:
    content = content.replace(
        "import React, { useState, useMemo, useEffect } from 'react';",
        "import React, { useState, useMemo, useEffect } from 'react';\nimport { Responsive, WidthProvider } from 'react-grid-layout';\nimport 'react-grid-layout/css/styles.css';\nimport 'react-resizable/css/styles.css';\nconst ResponsiveGridLayout = WidthProvider(Responsive);"
    )

state_str = '''
  const allWidgets = [
    { id: 'severity', label: 'Severity Distribution' },
    { id: 'status', label: 'Vulnerability Status' },
    { id: 'trend', label: 'Vulnerability Trend' },
    { id: 'cvssDist', label: 'CVSS Score Distribution' },
    { id: 'categories', label: 'Top Categories' },
    { id: 'topCwe', label: 'Top CWE Weaknesses' },
    { id: 'topCve', label: 'Top CVE IDs' },
    { id: 'assets', label: 'Most Affected Assets' },
    { id: 'newRepeat', label: 'New vs Repeat Findings' },
    { id: 'dataGrid', label: 'Vulnerabilities DataGrid' },
  ];
  const [visibleWidgets, setVisibleWidgets] = useState(allWidgets.map(w => w.id));
  const [layouts, setLayouts] = useState({
    lg: [
      { i: 'severity', x: 0, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'status', x: 6, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'trend', x: 0, y: 2, w: 8, h: 2, minW: 4, minH: 2 },
      { i: 'cvssDist', x: 8, y: 2, w: 4, h: 2, minW: 3, minH: 2 },
      { i: 'categories', x: 0, y: 4, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'topCwe', x: 6, y: 4, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'topCve', x: 0, y: 6, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'assets', x: 6, y: 6, w: 6, h: 2, minW: 3, minH: 2 },
      { i: 'newRepeat', x: 0, y: 8, w: 4, h: 2, minW: 3, minH: 2 },
      { i: 'dataGrid', x: 4, y: 8, w: 8, h: 3, minW: 6, minH: 3 },
    ]
  });
'''
if 'const allWidgets =' not in content:
    content = content.replace(
        "const [allVulnerabilities, setAllVulnerabilities] = useState([]);",
        "const [allVulnerabilities, setAllVulnerabilities] = useState([]);\n" + state_str
    )

customize_btn = '''
          <FormControl size="small" sx={{ minWidth: 200, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
            <InputLabel sx={{ color: 'text.secondary' }}>Customize Widgets</InputLabel>
            <Select
              multiple
              value={visibleWidgets}
              onChange={(e) => setVisibleWidgets(e.target.value)}
              input={<OutlinedInput label="Customize Widgets" />}
              renderValue={(selected) => ${selected.length} Widgets}
            >
              {allWidgets.map((w) => (
                <MenuItem key={w.id} value={w.id}>
                  <Checkbox checked={visibleWidgets.indexOf(w.id) > -1} />
                  <ListItemText primary={w.label} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
'''
if 'Customize Widgets' not in content:
    content = content.replace(
        "Export CSV\n          </Button>",
        "Export CSV\n          </Button>\n" + customize_btn
    )

match_start = re.search(r'\{\/\*.*ROW 1.*?\*\/\}', content)
match_end = re.search(r'\/\*.*?Empty State', content)

if match_start and match_end:
    start_idx = match_start.start()
    end_idx = content.rfind('</Box>', 0, match_end.start())
    
    grids_section = content[start_idx:end_idx]
    
    cards = re.findall(r'(<ChartCard.*?</ChartCard>)', grids_section, re.DOTALL)
    
    if len(cards) == 10:
        widgets_mapping = {
            'severity': cards[0],
            'status': cards[1],
            'trend': cards[2],
            'cvssDist': cards[3],
            'categories': cards[4],
            'topCwe': cards[5],
            'topCve': cards[6],
            'assets': cards[7],
            'newRepeat': cards[8],
            'dataGrid': cards[9]
        }

        new_grid_content = '''
      {/*  CUSTOMIZABLE GRID LAYOUT  */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        onLayoutChange={(currentLayout, allLayouts) => setLayouts(allLayouts)}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={170}
        draggableHandle=".MuiCardHeader-root, .MuiCardContent-root"
      >
        '''
        
        for w_id, w_content in widgets_mapping.items():
            new_grid_content += f'\n        <div key="{w_id}">\n          {{visibleWidgets.includes("{w_id}") && (\n            {w_content}\n          )}}\n        </div>'
                
        new_grid_content += '\n      </ResponsiveGridLayout>\n\n    '
        
        content = content[:start_idx] + new_grid_content + content[end_idx:]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Dashboard updated successfully!")
    else:
        print(f"Error: Found {len(cards)} ChartCards instead of 10.")
else:
    print("Could not find ROW 1 or Empty State markers")

