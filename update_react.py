import re

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("import { agencies, files } from '../data/seedData';", "import api from '../api/axios';")

state_add_pattern = r"(const \[chartFilter, setChartFilter\] = useState\(\{ key: null, value: null \}\);)"
new_state = r"\1\n  const [agencies, setAgencies] = useState([]);\n  const [files, setFiles] = useState([]);\n  const [allVulnerabilities, setAllVulnerabilities] = useState([]);"
content = re.sub(state_add_pattern, new_state, content)

new_use_effect = """useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [agenciesRes, reportsRes, vulnsRes] = await Promise.all([
          api.get('/api/agencies'),
          api.get('/api/reports'),
          api.get('/api/analytics/vulnerabilities')
        ]);
        
        setAgencies((agenciesRes.data.agencies || []).map(a => ({ id: a.agency_id, name: a.agency_name })));
        setFiles((reportsRes.data.reports || []).map(r => ({
          id: r.report_id,
          name: r.original_filename,
          agencyId: r.agency?.agency_id,
          date: r.created_at
        })));
        setAllVulnerabilities(vulnsRes.data.data || []);
      } catch (err) {
        console.error("Failed to fetch analytics data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);"""
content = content.replace("useEffect(() => {\n    const timer = setTimeout(() => setLoading(false), 800);\n    return () => clearTimeout(timer);\n  }, []);", new_use_effect)

old_filter = r"let vulns = \[\];\s*if \(viewMode === 'GLOBAL'\) \{\s*files\.forEach\(f => \{ vulns = vulns\.concat\(f\.vulnerabilities\); \}\);\s*\} else if \(viewMode === 'AGENCY'\) \{\s*const agencyFiles = files\.filter\(f => f\.agencyId === selectedAgencyId\);\s*agencyFiles\.forEach\(f => \{ vulns = vulns\.concat\(f\.vulnerabilities\); \}\);\s*\} else if \(viewMode === 'FILE'\) \{\s*const file = files\.find\(f => f\.id === selectedFileId\);\s*if \(file\) vulns = file\.vulnerabilities;\s*\}"

new_filter = """let vulns = [];
    if (viewMode === 'GLOBAL') {
      vulns = allVulnerabilities;
    } else if (viewMode === 'AGENCY') {
      vulns = allVulnerabilities.filter(v => v.agencyId === selectedAgencyId);
    } else if (viewMode === 'FILE') {
      vulns = allVulnerabilities.filter(v => v.fileId === selectedFileId);
    }"""
content = re.sub(old_filter, new_filter, content)

# 1. Remove instantiation
content = re.sub(r'\{/\*.*?ROW 6.*?AI Module 1.*?Standalone.*?\*/\}\s*<AISeverityPredictor />', '', content, flags=re.DOTALL)
# 2. Remove function definition
content = re.sub(r'/\*.*?AI Severity Predictor \(Standalone Module\).*?\*/.*?/\*\s*(.*?Empty State.*?)\s*\*/', r'/* \1 */', content, flags=re.DOTALL)

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
