import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'react-grid-layout' not in content:
    content = content.replace(
        "import React, { useEffect, useState } from 'react';",
        "import React, { useEffect, useState } from 'react';\nimport { Responsive, WidthProvider } from 'react-grid-layout';\nimport 'react-grid-layout/css/styles.css';\nimport 'react-resizable/css/styles.css';\nconst ResponsiveGridLayout = WidthProvider(Responsive);"
    )
    
    if 'FormControl' not in content:
        content = content.replace(
            "} from '@mui/material';",
            "  FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText, OutlinedInput\n} from '@mui/material';"
        )

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
        { i: 'topsis', x: 0, y: 2, w: 7, h: 3, minW: 4, minH: 3 },
        { i: 'anomalies', x: 7, y: 2, w: 5, h: 3, minW: 3, minH: 3 }
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

customize_btn = '''
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
            <InputLabel sx={{ color: 'text.secondary' }}>Customize Widgets</InputLabel>
            <Select
              multiple
              value={visibleWidgets}
              onChange={(e) => setVisibleWidgets(e.target.value)}
              input={<OutlinedInput label="Customize Widgets" />}
              renderValue={(selected) => \\ Widgets\}
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

if 'Customize Widgets' not in content:
    # Need to find the header block correctly to insert the customize button next to it or at the right side.
    # The header is typically <Box ...> ... <Typography ...> ... </Typography> <Typography ...> ... </Typography> </Box>
    # Let's replace the closing </Box> of the header with the new Box and then </Box>
    # Wait, the header is at the top. Let's find it safely.
    # The page structure usually starts with:
    # return (
    #   <Box>
    #     <Box sx={{ mb: 4 ... }}>
    #        <Typography variant="h4">...</Typography>
    #        <Typography variant="body2">...</Typography>
    #     </Box>
    
    # We can change the header wrapper to have display: flex, justifyContent: space-between, alignItems: flex-start
    # if it's not already.
    # Let's just append it after the body2 typography.
    content = content.replace(
        "Powered by Machine Learning models\n        </Typography>\n      </Box>",
        "Powered by Machine Learning models\n        </Typography>\n      </Box>\n" + customize_btn
    )
    # If the above doesn't match exactly because of formatting, we can use regex.
    content = re.sub(
        r'(Powered by Machine Learning models.*?</Typography>\s*</Box>)', 
        r'\1\n' + customize_btn.replace('\\', '\\\\'), # escape backslashes for re.sub
        content,
        flags=re.DOTALL
    )

cards = re.findall(r'(<Card\b[^>]*>[\s\S]*?</Card>)', content)
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

start_offset = content.find('<Grid container spacing={3}')
end_offset = content.rfind('</Box>', 0, content.rfind(');'))

if start_offset != -1 and end_offset != -1:
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
    
    content = content[:start_offset] + new_grid_content + content[end_offset:]
    print("Grids replaced")
else:
    print("Could not find grid start/end offsets")

# Fix any backtick escapes from Set-Content that might have been mangled
content = content.replace("renderValue={(selected) => \\ Widgets\}", "renderValue={(selected) => ${selected.length} Widgets}")
content = content.replace("renderValue={(selected) => \\\\\ Widgets\\\}", "renderValue={(selected) => ${selected.length} Widgets}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved.")
