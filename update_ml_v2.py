import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
if 'react-grid-layout' not in content:
    content = content.replace(
        "import React, { useEffect, useState } from 'react';",
        "import React, { useEffect, useState } from 'react';\nimport { Responsive, WidthProvider } from 'react-grid-layout';\nimport 'react-grid-layout/css/styles.css';\nimport 'react-resizable/css/styles.css';\nconst ResponsiveGridLayout = WidthProvider(Responsive);"
    )
    
    content = re.sub(r'Alert\s*\n*\s*\} from', 'Alert,\n  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, OutlinedInput\n} from', content)

state_str = '''
  const allWidgets = [
    { id: 'forecast', label: '6-Month Vulnerability Forecast' },
    { id: 'clustering', label: 'Agency Risk Clustering' },
    { id: 'topsis', label: 'Prioritized Action Queue' },
    { id: 'anomalies', label: 'Anomalous Agencies' }
  ];
  
  const [visibleWidgets, setVisibleWidgets] = useState(() => {
    const saved = localStorage.getItem('mlVisibleWidgets');
    return saved ? JSON.parse(saved) : allWidgets.map(w => w.id);
  });
  
  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem('mlLayouts');
    return saved ? JSON.parse(saved) : {
      lg: [
        { i: 'forecast', x: 0, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
        { i: 'clustering', x: 6, y: 0, w: 6, h: 2, minW: 3, minH: 2 },
        { i: 'topsis', x: 0, y: 2, w: 7, h: 3, minW: 4, minH: 2 },
        { i: 'anomalies', x: 7, y: 2, w: 5, h: 3, minW: 3, minH: 2 }
      ]
    };
  });

  useEffect(() => {
    localStorage.setItem('mlVisibleWidgets', JSON.stringify(visibleWidgets));
  }, [visibleWidgets]);

  useEffect(() => {
    localStorage.setItem('mlLayouts', JSON.stringify(layouts));
  }, [layouts]);
'''

if 'const allWidgets =' not in content:
    content = content.replace(
        "const [loading, setLoading] = useState(true);",
        "const [loading, setLoading] = useState(true);\n" + state_str
    )

customize_btn = r'''
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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
        </Box>
'''

# The title block
title_block = r'''        <Box>
          <Typography variant="h4" fontWeight={800}>AI Risk Analytics (Air-Gapped)</Typography>
          <Typography variant="body2" color="text.secondary">
            Mathematical Forecasting, Clustering, and Task Prioritization without external models
          </Typography>
        </Box>'''

new_title_block = r'''        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
          <Box>
            <Typography variant="h4" fontWeight={800}>AI Risk Analytics (Air-Gapped)</Typography>
            <Typography variant="body2" color="text.secondary">
              Mathematical Forecasting, Clustering, and Task Prioritization without external models
            </Typography>
          </Box>
          ''' + customize_btn + r'''
        </Box>'''

if 'Customize Widgets' not in content:
    content = content.replace(title_block, new_title_block)


# Grid section replacement
cards = re.findall(r'(<Card\b[^>]*>[\s\S]*?</Card>)', content)
# Skip cards that are in the loading skeleton if there were any, but skeletons are just <Skeleton> tags.
# There should be exactly 4 cards in MLAnalyticsDashboardPage.
print(f"Found {len(cards)} cards")

def get_card(title_pattern):
    for card in cards:
        if re.search(title_pattern, card):
            return card
    return None

widgets_mapping = {
    'forecast': get_card(r'6-Month Vulnerability Forecast'),
    'clustering': get_card(r'Agency Risk Clustering'),
    'topsis': get_card(r'Prioritized Action Queue'),
    'anomalies': get_card(r'Anomalous Agencies')
}

grid_start_tag = '<Grid container spacing={3} sx={{ mb: 4 }}>'

start_idx = content.find(grid_start_tag)
if start_idx != -1:
    # Find the end of the second grid container.
    # We can just find the end of the return statement.
    end_idx = content.find('</Box>\n    </Box>\n  );\n}')
    if end_idx == -1:
        end_idx = content.find('</Box>\n  );\n}')
    
    new_grid_content = '''
      {/*  CUSTOMIZABLE GRID LAYOUT  */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        onLayoutChange={(currentLayout, allLayouts) => setLayouts(allLayouts)}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={170}
        draggableHandle=".MuiCardContent-root"
      >
    '''
    
    for w_id, w_content in widgets_mapping.items():
        if w_content:
            new_grid_content += f'\n        <div key="{w_id}">\n          {{visibleWidgets.includes("{w_id}") && (\n            {w_content}\n          )}}\n        </div>'
    
    new_grid_content += '\n      </ResponsiveGridLayout>\n    '
    
    content = content[:start_idx] + new_grid_content + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved.")
