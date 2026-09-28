"""
AI Pipeline Service
-------------------
Standalone FastAPI microservice that receives a report file,
runs a dummy AI analysis pipeline, and returns structured JSON results.
"""

import asyncio
import hashlib
import random
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Pipeline Service",
    description="Dummy AI analysis pipeline for cyber-audit reports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _generate_dummy_results(report_id: str, file_bytes: bytes, filename: str) -> dict:
    """Return the exact JSON structure provided by the user with zero additional information."""
    return {
  "_meta": {
    "pipeline_version": "1.0.0",
    "source_file": "CERTIN_AUDIT_SAMPLE_2026.pdf",
    "extraction_timestamp": "2026-09-25T10:30:00Z",
    "llm_model": "gpt-4o",
    "extraction_mode": "hybrid",
    "tables_extracted": 8,
    "images_extracted": 3
  },
  "metadata": {
    "document_title": "Information Security Audit Report",
    "document_id": "AUD-2026-001",
    "document_version": "1.0",
    "document_classification": "Confidential",
    "organization_audited": "National Digital Services Corporation",
    "auditing_organization": "SecureTech Cyber Security Pvt Ltd",
    "audit_type": "Vulnerability Assessment and Penetration Testing",
    "report_type": "Final Audit Report",
    "release_date": "2026-09-20",
    "prepared_by": "Rahul Sharma",
    "reviewed_by": "Ankit Verma",
    "approved_by": "Neha Gupta",
    "released_by": "Amit Singh",
    "standards_referenced": [
      "CERT-In Guidelines",
      "ISO/IEC 27001:2022",
      "OWASP Top 10 2021",
      "CIS Controls v8"
    ]
  },
  "scope": {
    "description": "Security assessment of the organization's public-facing web applications, internal network, and supporting infrastructure to identify vulnerabilities and recommend remediation measures.",
    "assets_tested": [
      {
        "sr_no": "1",
        "asset_name": "Citizen Services Portal",
        "asset_type": "Web Application",
        "url": "https://portal.example.com",
        "internal_ip": "10.10.1.10",
        "public_ip": "203.0.113.10",
        "location": "New Delhi Data Center",
        "criticality": "Critical",
        "version": "2.4.1",
        "other_details": "Public-facing portal used for citizen service requests."
      },
      {
        "sr_no": "2",
        "asset_name": "Payment Gateway",
        "asset_type": "Web Application",
        "url": "https://payments.example.com",
        "internal_ip": "10.10.1.20",
        "public_ip": "203.0.113.20",
        "location": "New Delhi Data Center",
        "criticality": "Critical",
        "version": "3.1.0",
        "other_details": "Handles payment transactions and payment status queries."
      },
      {
        "sr_no": "3",
        "asset_name": "Application Database Server",
        "asset_type": "Database Server",
        "url": None,
        "internal_ip": "10.10.2.15",
        "public_ip": "",
        "location": "Primary Data Center",
        "criticality": "High",
        "version": "PostgreSQL 15",
        "other_details": "Stores application records and user information."
      }
    ],
    "testing_period": {
      "start_date": "2026-09-10",
      "end_date": "2026-09-15"
    },
    "assumptions": "Testing was conducted using authorized access and the assets provided by the audited organization. Production data was not intentionally modified. All findings require confirmation and remediation validation by the concerned organization."
  },
  "audit_team": [
    {
      "name": "Rahul Sharma",
      "designation": "Lead Security Auditor",
      "organization": "SecureTech Cyber Security Pvt Ltd",
      "email": "rahul.sharma@example.com",
      "certifications": "CEH, ISO 27001 Lead Auditor",
      "listed_on_certin": "Yes - Dummy Data"
    },
    {
      "name": "Priya Verma",
      "designation": "Security Analyst",
      "organization": "SecureTech Cyber Security Pvt Ltd",
      "email": "priya.verma@example.com",
      "certifications": "OSCP",
      "listed_on_certin": "Yes - Dummy Data"
    }
  ],
  "tools_used": [
    {
      "name": "Nmap",
      "version": "7.95",
      "license_type": "Open Source",
      "description": "Network discovery and port scanning."
    },
    {
      "name": "OWASP ZAP",
      "version": "2.16.0",
      "license_type": "Open Source",
      "description": "Web application security testing and vulnerability identification."
    },
    {
      "name": "Burp Suite",
      "version": "2026.1",
      "license_type": "Commercial",
      "description": "Web application testing and HTTP traffic analysis."
    },
    {
      "name": "Nessus",
      "version": "10.8",
      "license_type": "Commercial",
      "description": "Infrastructure vulnerability scanning and configuration assessment."
    }
  ],
  "methodology": "The audit followed a structured methodology consisting of scope definition, asset discovery, vulnerability scanning, manual verification, risk assessment, evidence collection, and report preparation. Findings were categorized according to severity and accompanied by remediation recommendations.",
  "executive_summary": {
    "summary_text": "The assessment identified five vulnerabilities across the tested assets. The findings include one critical, one high, two medium, and one low severity issue. The audited organization should prioritize remediation based on severity, business impact, and exposure. All findings in this report are fictional and intended for testing the ingestion and analytics pipeline.",
    "total_vulnerabilities": 5,
    "critical_count": 1,
    "high_count": 1,
    "medium_count": 2,
    "low_count": 1,
    "informational_count": 0,
    "summary_findings": [
      {
        "sr_no": "1",
        "vulnerability_title": "SQL Injection",
        "severity": "Critical",
        "affected_asset": "Citizen Services Portal",
        "status": "Open",
        "new_or_repeat": "New"
      },
      {
        "sr_no": "2",
        "vulnerability_title": "Broken Access Control",
        "severity": "High",
        "affected_asset": "Payment Gateway",
        "status": "Open",
        "new_or_repeat": "New"
      },
      {
        "sr_no": "3",
        "vulnerability_title": "Missing Security Headers",
        "severity": "Medium",
        "affected_asset": "Citizen Services Portal",
        "status": "Open",
        "new_or_repeat": "Repeat"
      },
      {
        "sr_no": "4",
        "vulnerability_title": "Outdated Software Component",
        "severity": "Medium",
        "affected_asset": "Application Database Server",
        "status": "In Progress",
        "new_or_repeat": "New"
      },
      {
        "sr_no": "5",
        "vulnerability_title": "Information Disclosure",
        "severity": "Low",
        "affected_asset": "Payment Gateway",
        "status": "Open",
        "new_or_repeat": "Repeat"
      }
    ]
  },
  "vulnerabilities": [
    {
      "report id": "AUD-2026-001",
      "id": "VUL-001",
      "vulnerability_title": "SQL Injection",
      "category": "Injection",
      "severity": "Critical",
      "cvss_score": 9.8,
      "cve_ids": [],
      "cwe_ids": [
        "CWE-89"
      ],
      "affected_assets": [
        "Citizen Services Portal"
      ],
      "status": "Open",
      "detailed_observation": "The assessment identified insufficient input validation in a database-backed application function. The issue may allow user-supplied input to interfere with database queries.",
      "description": "SQL injection occurs when untrusted input is incorporated into SQL queries without appropriate parameterization or validation.",
      "impact": "Potential unauthorized access to sensitive database records, modification of data, and compromise of application confidentiality and integrity.",
      "recommendation": "Use parameterized queries or prepared statements, implement server-side input validation, apply least-privilege database permissions, and conduct security testing after remediation.",
      "proof_of_concept": "Fictional placeholder: input validation testing indicated that specially crafted input may alter database query behavior. No real production payload is included.",
      "reproduction_steps": None,
      "reference": "https://owasp.org/www-community/attacks/SQL_Injection",
      "new_or_repeat": "New",
      "revalidation_status": None,
      "additional meta": {
        "discovery_method": "Manual Testing",
        "confidence": "High",
        "business_impact": "High",
        "remediation_priority": "P1",
        "department": "IT Security"
      }
    },
    {
      "report id": "AUD-2026-001",
      "id": "VUL-002",
      "vulnerability_title": "Broken Access Control",
      "category": "Access Control",
      "severity": "High",
      "cvss_score": 8.1,
      "cve_ids": [],
      "cwe_ids": [
        "CWE-284",
        "CWE-639"
      ],
      "affected_assets": [
        "Payment Gateway"
      ],
      "status": "Open",
      "detailed_observation": "Authorization checks were found to be insufficient in a fictional payment transaction endpoint. The application may not consistently verify whether a user is authorized to access a requested transaction.",
      "description": "Broken access control occurs when an application fails to properly enforce restrictions on authenticated users.",
      "impact": "Unauthorized access to transaction details, exposure of customer information, and potential violation of data confidentiality.",
      "recommendation": "Enforce server-side authorization checks on every sensitive request, validate object ownership, implement role-based access control, and maintain audit logs.",
      "proof_of_concept": "Fictional placeholder: an authorization test using sample accounts indicated inconsistent access restrictions.",
      "reproduction_steps": None,
      "reference": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
      "new_or_repeat": "New",
      "revalidation_status": None,
      "additional meta": {
        "discovery_method": "Manual Testing",
        "confidence": "High",
        "business_impact": "High",
        "remediation_priority": "P2",
        "department": "Application Development"
      }
    },
    {
      "report id": "AUD-2026-001",
      "id": "VUL-003",
      "vulnerability_title": "Missing Security Headers",
      "category": "Security Misconfiguration",
      "severity": "Medium",
      "cvss_score": 5.3,
      "cve_ids": [],
      "cwe_ids": [
        "CWE-693"
      ],
      "affected_assets": [
        "Citizen Services Portal"
      ],
      "status": "Open",
      "detailed_observation": "The application response was found to lack certain recommended HTTP security headers, including Content-Security-Policy and Strict-Transport-Security.",
      "description": "Missing security headers may reduce browser-side protection against certain classes of web attacks.",
      "impact": "Increased exposure to client-side attacks, reduced transport security enforcement, and weaker browser security controls.",
      "recommendation": "Configure appropriate HTTP security headers, establish a restrictive Content-Security-Policy, and enforce HTTPS using Strict-Transport-Security after validating deployment requirements.",
      "proof_of_concept": "Fictional placeholder: HTTP response header review identified missing recommended security headers.",
      "reproduction_steps": None,
      "reference": "https://owasp.org/www-project-secure-headers/",
      "new_or_repeat": "Repeat",
      "revalidation_status": None,
      "additional meta": {
        "discovery_method": "Automated Scan",
        "confidence": "High",
        "business_impact": "Medium",
        "remediation_priority": "P3",
        "department": "Web Operations"
      }
    },
    {
      "report id": "AUD-2026-001",
      "id": "VUL-004",
      "vulnerability_title": "Outdated Software Component",
      "category": "Vulnerable and Outdated Components",
      "severity": "Medium",
      "cvss_score": 6.1,
      "cve_ids": [
        "CVE-2024-0000"
      ],
      "cwe_ids": [
        "CWE-1104"
      ],
      "affected_assets": [
        "Application Database Server"
      ],
      "status": "In Progress",
      "detailed_observation": "The server inventory indicates that a software component is running an older version that requires a patch review. The CVE identifier is a dummy placeholder and is not a real vulnerability reference.",
      "description": "Using outdated software components can expose systems to publicly documented vulnerabilities and security defects.",
      "impact": "Potential unauthorized access, service disruption, or compromise depending on the actual component vulnerability and system configuration.",
      "recommendation": "Verify the installed component and version, consult the vendor security advisories, apply supported security updates, and perform regression testing.",
      "proof_of_concept": "Fictional placeholder: version inventory comparison indicated that the installed component may require security updates.",
      "reproduction_steps": None,
      "reference": "https://nvd.nist.gov/",
      "new_or_repeat": "New",
      "revalidation_status": None,
      "additional meta": {
        "discovery_method": "Version Detection",
        "confidence": "Medium",
        "business_impact": "Medium",
        "remediation_priority": "P3",
        "department": "Infrastructure"
      }
    },
    {
      "report id": "AUD-2026-001",
      "id": "VUL-005",
      "vulnerability_title": "Information Disclosure",
      "category": "Security Misconfiguration",
      "severity": "Low",
      "cvss_score": 3.7,
      "cve_ids": [],
      "cwe_ids": [
        "CWE-200"
      ],
      "affected_assets": [
        "Payment Gateway"
      ],
      "status": "Open",
      "detailed_observation": "The application error response exposes technical information, including a fictional framework version and internal error details.",
      "description": "Information disclosure occurs when an application reveals sensitive technical or operational information to unauthorized users.",
      "impact": "Exposed information may assist an attacker in identifying technology components and planning further attacks.",
      "recommendation": "Disable detailed error messages in production, implement generic user-facing error responses, and retain detailed diagnostic logs in restricted server-side storage.",
      "proof_of_concept": "Fictional placeholder: a controlled invalid request returned a detailed application error response.",
      "reproduction_steps": None,
      "reference": "https://cwe.mitre.org/data/definitions/200.html",
      "new_or_repeat": "Repeat",
      "revalidation_status": None,
      "additional meta": {
        "discovery_method": "Manual Testing",
        "confidence": "High",
        "business_impact": "Low",
        "remediation_priority": "P4",
        "department": "Application Development"
      }
    }
  ],
  "risk_rating_criteria": {
    "critical": "CVSS score 9.0-10.0. Immediate remediation required due to potentially severe business impact.",
    "high": "CVSS score 7.0-8.9. Remediation should be prioritized within the defined remediation period.",
    "medium": "CVSS score 4.0-6.9. Remediation should be scheduled according to risk and business impact.",
    "low": "CVSS score 0.1-3.9. Remediation should be performed as part of routine security maintenance.",
    "informational": "No direct security vulnerability identified. Observations are provided for awareness and security improvement."
  },
  "appendices": {
    "acronyms": {
      "VAPT": "Vulnerability Assessment and Penetration Testing",
      "CERT-In": "Indian Computer Emergency Response Team",
      "CVSS": "Common Vulnerability Scoring System",
      "CVE": "Common Vulnerabilities and Exposures",
      "CWE": "Common Weakness Enumeration",
      "OWASP": "Open Worldwide Application Security Project",
      "IP": "Internet Protocol"
    },
    "site_structure": {
      "root": "National Digital Services Corporation",
      "departments": [
        {
          "name": "IT Security",
          "assets": [
            "Citizen Services Portal",
            "Payment Gateway"
          ]
        },
        {
          "name": "Infrastructure",
          "assets": [
            "Application Database Server"
          ]
        }
      ]
    },
    "risk_assessment_matrix": [
      {
        "impact": "Critical",
        "likelihood": "High",
        "risk_severity": "Critical"
      },
      {
        "impact": "High",
        "likelihood": "Medium",
        "risk_severity": "High"
      },
      {
        "impact": "Medium",
        "likelihood": "Medium",
        "risk_severity": "Medium"
      },
      {
        "impact": "Low",
        "likelihood": "Low",
        "risk_severity": "Low"
      }
    ],
    "disclaimer": "This is a fictional sample report created exclusively for software development, ingestion pipeline testing, database schema validation, and dashboard visualization. It is not an actual CERT-In audit report or evidence of a real security assessment. The CVE identifier and organizational details are dummy data."
  }
}


@app.post("/run")
async def run_pipeline(
    report_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Run the AI analysis pipeline on the uploaded report file.
    Returns structured JSON with analysis results.
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown"

    # Simulate AI processing time (2-3 seconds)
    await asyncio.sleep(random.uniform(2.0, 3.0))

    results = _generate_dummy_results(report_id, file_bytes, filename)
    #write your ai logic

    return results


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-pipeline"}
