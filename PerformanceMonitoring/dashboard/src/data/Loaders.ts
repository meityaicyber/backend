export interface RankingSummary {
  metadata: {
    total_organisations: number;
    assessable_organisations: number;
    provenance: Record<string, string>;
  };
  top_10: OrganisationScore[];
  bottom_10: OrganisationScore[];
}

export interface OrganisationScore {
  organisation_id: string;
  rank: number | null;
  performance_score: number;
  assessment_status: string;
  missing_features: string[];
  renewal_prediction?: {
    class: string;
    probability: number;
    boundary_status: string;
  };
  provenance: Record<string, string>;
}

export interface Dataset {
  data: Array<{
    organisation_id: string;
    features: Record<string, any>;
    renewal_outcome: number;
  }>;
}

export interface ModelComparison {
  [modelName: string]: {
    accuracy: number;
    macro_f1: number;
  };
}

export interface VersionRegistry {
  current_versions: Record<string, string>;
  history: Array<{
    timestamp: string;
    change: string;
    approver: string;
    updated_components: Array<{
      component: string;
      old_version: string;
      new_version: string;
    }>;
  }>;
}

export interface TestReport {
  summary: {
    passed: number;
    failed: number;
    total: number;
    duration?: number;
  };
  tests: Array<{
    nodeid: string;
    outcome: 'passed' | 'failed' | 'skipped';
    call?: { duration?: number; crash?: { message: string } };
  }>;
}

// Data loaders
export const fetchData = async <T>(url: string): Promise<T> => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error loading data from ${url}:`, error);
    throw error;
  }
};

export const loadRankingSummary = () => fetchData<RankingSummary>('/data/ranking_summary.json');
export const loadOrganisationScores = () => fetchData<OrganisationScore[]>('/data/organisation_scores.json');
export const loadDataset = () => fetchData<Dataset>('/data/sample_dataset.json');
export const loadModelComparison = () => fetchData<ModelComparison>('/data/comparison_summary.json');
export const loadVersionRegistry = () => fetchData<VersionRegistry>('/data/version_registry.json');
export const loadTestReport = () => fetchData<TestReport>('/data/test_report.json');
