import re

file_path = r'c:\Main Project\Module\backend\frontend\src\pages\MLAnalyticsDashboardPage.jsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix anomalies card
content = content.replace(
    '''<Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ErrorOutline sx={{ color: '#FF9100' }} />
                <Typography variant="h6" fontWeight={700}>Anomalous Agencies (Isolation Forest)</Typography>''',
    '''<Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ErrorOutline sx={{ color: '#FF9100' }} />
                <Typography variant="h6" fontWeight={700}>Anomalous Agencies (Isolation Forest)</Typography>'''
)

# Fix topsis card
content = content.replace(
    '''<Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ReportProblem sx={{ color: '#FF1744' }} />
                <Typography variant="h6" fontWeight={700}>Prioritized Action Queue (TOPSIS)</Typography>''',
    '''<Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                <ReportProblem sx={{ color: '#FF1744' }} />
                <Typography variant="h6" fontWeight={700}>Prioritized Action Queue (TOPSIS)</Typography>'''
)

# Fix TableContainers for these two specifically.
# Since there are multiple TableContainers, let's just replace all <TableContainer> with <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
# But only if it's currently <TableContainer> exactly.
content = content.replace('<TableContainer>', "<TableContainer sx={{ flex: 1, overflowY: 'auto' }}>")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Scroll fixed")
