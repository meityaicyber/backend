import re

file_path = 'c:/Main Project/Modules/backend/frontend/src/pages/ReportsPage.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add the new components right before PipelineResultsDialog
new_components = """
const JsonNode = ({ label, value, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  
  if (value === null || value === undefined) {
    return (
      <Box sx={{ display: 'flex', py: 0.5 }}>
        <Typography variant="body2" sx={{ color: '#90caf9', mr: 1 }}>"{label}":</Typography>
        <Typography variant="body2" sx={{ color: '#757575' }}>null</Typography>
      </Box>
    );
  }

  if (typeof value !== 'object') {
    let color = '#a5d6a7';
    if (typeof value === 'number') color = '#ffab91';
    if (typeof value === 'boolean') color = '#ce93d8';
    return (
      <Box sx={{ display: 'flex', py: 0.5, alignItems: 'flex-start' }}>
        <Typography variant="body2" sx={{ color: '#90caf9', mr: 1 }}>"{label}":</Typography>
        <Typography variant="body2" sx={{ color, wordBreak: 'break-all' }}>
          {typeof value === 'string' ? `"${value}"` : String(value)}
        </Typography>
      </Box>
    );
  }

  const isArray = Array.isArray(value);
  const keys = Object.keys(value);

  if (keys.length === 0) {
    return (
      <Box sx={{ display: 'flex', py: 0.5 }}>
        <Typography variant="body2" sx={{ color: '#90caf9', mr: 1 }}>"{label}":</Typography>
        <Typography variant="body2" sx={{ color: '#757575' }}>{isArray ? '[]' : '{}'}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 0.5 }}>
      <Box 
        onClick={() => setExpanded(!expanded)}
        sx={{ 
          display: 'flex', alignItems: 'center', cursor: 'pointer', 
          py: 0.5, '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' }, borderRadius: 1 
        }}
      >
        <Typography variant="body2" sx={{ color: '#fff', fontSize: '0.7rem', width: 20, textAlign: 'center' }}>
          {expanded ? '▼' : '▶'}
        </Typography>
        <Typography variant="body2" sx={{ color: '#90caf9', fontWeight: 600 }}>
          "{label}": {isArray ? `[${keys.length} items]` : '{ ... }'}
        </Typography>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ pl: 2, borderLeft: '1px dashed rgba(255,255,255,0.15)', ml: 1, mt: 0.5 }}>
          {keys.map((key) => (
            <JsonNode key={key} label={key} value={value[key]} />
          ))}
        </Box>
      </Collapse>
    </Box>
  );
};

const JsonSection = ({ sectionKey, sectionData }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <Card elevation={0} sx={{ bgcolor: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 2 }}>
      <Box 
        onClick={() => setExpanded(!expanded)}
        sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}
      >
        <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#00D4FF', textTransform: 'uppercase', letterSpacing: 1 }}>
          {sectionKey.replace(/_/g, ' ')}
        </Typography>
        {expanded ? <ExpandLess /> : <ExpandMore />}
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 2, pt: 0, borderTop: '1px solid rgba(255,255,255,0.05)', bgcolor: 'rgba(0,0,0,0.2)', overflowX: 'auto' }}>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
             {typeof sectionData === 'object' && sectionData !== null ? (
               Object.keys(sectionData).map(subKey => (
                 <JsonNode key={subKey} label={subKey} value={sectionData[subKey]} defaultExpanded={false} />
               ))
             ) : (
                <Typography variant="body2" sx={{ color: '#ccc' }}>{String(sectionData)}</Typography>
             )}
          </Box>
        </Box>
      </Collapse>
    </Card>
  );
};

const JsonSectionView = ({ data }) => {
  if (!data || typeof data !== 'object') return null;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      {Object.keys(data).map((key) => (
        <JsonSection key={key} sectionKey={key} sectionData={data[key]} />
      ))}
    </Box>
  );
};
"""

# Insert before `function PipelineResultsDialog`
# Note: we need to find the `function PipelineResultsDialog` line
insert_index = content.find('function PipelineResultsDialog')
if insert_index != -1:
    content = content[:insert_index] + new_components + content[insert_index:]
else:
    print("Could not find function PipelineResultsDialog")


# Now replace tabValue === 1 section
old_tab_1 = """        {tabValue === 1 && (
          <Box sx={{ p: 2, bgcolor: 'rgba(0,0,0,0.5)', borderRadius: 2, overflowX: 'auto', maxHeight: 600, overflowY: 'auto' }}>
            <pre style={{ margin: 0, color: '#00D4FF', fontSize: '0.85rem' }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </Box>
        )}"""

new_tab_1 = """        {tabValue === 1 && (
          <Box sx={{ p: 1, maxHeight: 600, overflowY: 'auto' }}>
            <JsonSectionView data={results} />
          </Box>
        )}"""

content = content.replace(old_tab_1, new_tab_1)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
