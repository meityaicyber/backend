import re

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove <AISeverityPredictor /> instantiation
content = re.sub(r'\{/\*.*ROW 6.*AI Module 1.*\*/\}\s*<AISeverityPredictor />', '', content)

# 2. Remove the AISeverityPredictor function definition
content = re.sub(r'/\*.*AI Severity Predictor \(Standalone Module\).*\*/[\s\S]*', '', content)

with open('frontend/src/pages/AnalyticsDashboardPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content.strip() + '\n')
