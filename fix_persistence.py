import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\AnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace visibleWidgets state
visible_widgets_search = "const [visibleWidgets, setVisibleWidgets] = useState(allWidgets.map(w => w.id));"
visible_widgets_replace = '''const [visibleWidgets, setVisibleWidgets] = useState(() => {
    const saved = localStorage.getItem('analyticsVisibleWidgets');
    return saved ? JSON.parse(saved) : allWidgets.map(w => w.id);
  });
  
  useEffect(() => {
    localStorage.setItem('analyticsVisibleWidgets', JSON.stringify(visibleWidgets));
  }, [visibleWidgets]);'''

if visible_widgets_search in content:
    content = content.replace(visible_widgets_search, visible_widgets_replace)

# 2. Replace layouts state
layout_search = '''  const [layouts, setLayouts] = useState({
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
  });'''

layout_replace = '''  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem('analyticsLayouts');
    return saved ? JSON.parse(saved) : {
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
    };
  });

  useEffect(() => {
    localStorage.setItem('analyticsLayouts', JSON.stringify(layouts));
  }, [layouts]);'''

if layout_search in content:
    content = content.replace(layout_search, layout_replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Persistence added successfully!")
