export interface DatasetProfileColumn {
  name: string;
  dtype: string;
  null_count: number;
  null_pct: number;
  unique_count: number;
  sample_values: string[];
}

export interface DatasetProfile {
  shape: { rows: number; columns: number };
  columns: DatasetProfileColumn[];
  duplicate_rows: number;
  numeric_columns: string[];
  datetime_columns: string[];
}

export interface SampleDatasetInfo {
  key: string;
  label: string;
  description: string;
  format: string;
}

export interface DatasetLoadResponse {
  session_id: string;
  dataset_name: string;
  profile: DatasetProfile;
  preview: Record<string, string>[];
  columns: string[];
}

export interface AttemptOut {
  attempt_number: number;
  success: boolean;
  code: string;
  error: string | null;
  retrieved_doc_sources: string[];
}

export interface ResultTable {
  type: "dataframe" | "dict" | "text";
  columns?: string[] | null;
  data: unknown;
}

export interface AskResponse {
  success: boolean;
  question: string;
  insights: string | null;
  result: ResultTable | null;
  chart_urls: string[];
  attempts: AttemptOut[];
  final_code: string | null;
  report_url: string | null;
}

export interface HealthResponse {
  status: string;
  model: string;
  max_self_heal_attempts: number;
}
