"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ClipboardCheck,
} from "lucide-react";

import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type GazetteRule = {
  rule_type?: string;
  vehicle_type?: string;
  fuel_type?: string;
  category_code?: string;
  hs_code?: string;
  engine_min?: number;
  engine_max?: number;
  power_kw_min?: number;
  power_kw_max?: number;
  age_years_min?: number;
  age_years_max?: number;
  excise_type?: string;
  excise_rate?: number;
  customs_percent?: number;
  surcharge_percent?: number;
  excise_percent?: number;
  excise_per_kw_amount?: number;
  vat_percent?: number;
  pal_percent?: number;
  cess_percent?: number;
  cess_type?: string;
  cess_value?: number;
  luxury_tax_threshold?: number;
  luxury_tax_percent?: number;
  threshold_value?: number;
  rate_percent?: number;
  applies_to?: string;
  name?: string;
  apply_on?: string;
  notes?: string;
};

type GazetteRuleDraft = {
  rule_type: string;
  vehicle_type: string;
  fuel_type: string;
  category_code: string;
  hs_code: string;
  engine_min: string;
  engine_max: string;
  power_kw_min: string;
  power_kw_max: string;
  age_years_min: string;
  age_years_max: string;
  excise_type: string;
  excise_rate: string;
  customs_percent: string;
  surcharge_percent: string;
  excise_percent: string;
  excise_per_kw_amount: string;
  vat_percent: string;
  pal_percent: string;
  cess_percent: string;
  cess_type: string;
  cess_value: string;
  luxury_tax_threshold: string;
  luxury_tax_percent: string;
  threshold_value: string;
  rate_percent: string;
  applies_to: string;
  name: string;
  apply_on: string;
  notes: string;
};

type GazettePreview = {
  gazette_no?: string;
  effective_date?: string;
  rules?: GazetteRule[];
  text?: string;
  tables?: unknown[];
  error?: string;
};

type GazetteUploadResponse = {
  gazette_id: string;
  gazette_no: string;
  effective_date: string | null;
  rules_count: number;
  confidence: number;
  status: string;
  preview: GazettePreview;
  message?: string | null;
};

type CatalogUploadResponse = {
  dataset: string;
  effective_date: string;
  uploaded_rows: number;
  superseded_rows: number;
  preview_rows: Record<string, string | number | boolean | null>[];
  message: string;
};

type GazetteDetailResponse = {
  gazette_id: string;
  gazette_no: string;
  effective_date: string | null;
  rules_count: number;
  status: string;
  preview: GazettePreview;
  rejection_reason?: string | null;
  uploaded_by?: string | null;
  approved_by?: string | null;
  created_at: string;
};

type GazetteHistoryItem = {
  id: string;
  gazette_no: string;
  effective_date: string | null;
  status: string;
  rules_count: number;
  created_at: string;
  uploaded_by?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
};

type GazetteHistoryResponse = {
  items: GazetteHistoryItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
};

const STATUS_STYLES: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
  APPROVED: "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
  REJECTED: "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
  NEEDS_MANUAL_REVIEW: "bg-orange-100 text-orange-800 ring-1 ring-orange-200",
};

const MAX_FILE_SIZE_MB = 50;

function createEmptyRuleDraft(ruleType = "VEHICLE_TAX"): GazetteRuleDraft {
  return {
    rule_type: ruleType,
    vehicle_type: ruleType === "VEHICLE_TAX" ? "SEDAN" : "",
    fuel_type: ruleType === "VEHICLE_TAX" ? "PETROL" : "",
    category_code: "",
    hs_code: "",
    engine_min: "0",
    engine_max: "999999",
    power_kw_min: "",
    power_kw_max: "",
    age_years_min: "",
    age_years_max: "",
    excise_type: "",
    excise_rate: "",
    customs_percent: "0",
    surcharge_percent: "0",
    excise_percent: "0",
    excise_per_kw_amount: "",
    vat_percent: "15",
    pal_percent: "0",
    cess_percent: "0",
    cess_type: "",
    cess_value: "",
    luxury_tax_threshold: "",
    luxury_tax_percent: "",
    threshold_value: "",
    rate_percent: "",
    applies_to: "",
    name: "",
    apply_on: "CIF",
    notes: "",
  };
}

function statusBadge(status: string) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        STATUS_STYLES[status] ??
          "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
      )}
    >
      {status}
    </span>
  );
}

function formatDate(value: string | null | undefined) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function GazetteManagementPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [gazetteNo, setGazetteNo] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [catalogEffectiveDate, setCatalogEffectiveDate] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] =
    useState<GazetteUploadResponse | null>(null);
  const [catalogUploadResult, setCatalogUploadResult] =
    useState<CatalogUploadResponse | null>(null);
  const [catalogEditableRows, setCatalogEditableRows] = useState<
    Record<string, string | number | boolean | null>[]
  >([]);
  const [catalogSavingRowId, setCatalogSavingRowId] = useState<string | null>(
    null,
  );
  const [catalogDeletingRowId, setCatalogDeletingRowId] = useState<
    string | null
  >(null);
  const [catalogSavingAll, setCatalogSavingAll] = useState(false);
  const [catalogChangeReason, setCatalogChangeReason] = useState("");

  const [history, setHistory] = useState<GazetteHistoryResponse | null>(null);
  const [historyStatus, setHistoryStatus] = useState("");
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const [selectedGazette, setSelectedGazette] =
    useState<GazetteDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [editableEffectiveDate, setEditableEffectiveDate] = useState("");
  const [editableRules, setEditableRules] = useState<GazetteRuleDraft[]>([]);
  const [reviewSaving, setReviewSaving] = useState(false);

  const buildRuleDrafts = useCallback(
    (inputRules: GazetteRule[] | undefined) => {
      if (!Array.isArray(inputRules)) return [];
      return inputRules.map((rule) => ({
        rule_type: String(rule.rule_type ?? "VEHICLE_TAX"),
        vehicle_type: String(rule.vehicle_type ?? ""),
        fuel_type: String(rule.fuel_type ?? ""),
        category_code: String(rule.category_code ?? ""),
        hs_code: String(rule.hs_code ?? ""),
        engine_min: String(rule.engine_min ?? 0),
        engine_max: String(rule.engine_max ?? 999999),
        power_kw_min: String(rule.power_kw_min ?? ""),
        power_kw_max: String(rule.power_kw_max ?? ""),
        age_years_min: String(rule.age_years_min ?? ""),
        age_years_max: String(rule.age_years_max ?? ""),
        excise_type: String(rule.excise_type ?? ""),
        excise_rate: String(rule.excise_rate ?? ""),
        customs_percent: String(rule.customs_percent ?? 0),
        surcharge_percent: String(rule.surcharge_percent ?? 0),
        excise_percent: String(rule.excise_percent ?? 0),
        excise_per_kw_amount: String(rule.excise_per_kw_amount ?? ""),
        vat_percent: String(rule.vat_percent ?? 15),
        pal_percent: String(rule.pal_percent ?? 0),
        cess_percent: String(rule.cess_percent ?? 0),
        cess_type: String(rule.cess_type ?? ""),
        cess_value: String(rule.cess_value ?? ""),
        luxury_tax_threshold: String(rule.luxury_tax_threshold ?? ""),
        luxury_tax_percent: String(rule.luxury_tax_percent ?? ""),
        threshold_value: String(rule.threshold_value ?? ""),
        rate_percent: String(rule.rate_percent ?? ""),
        applies_to: String(rule.applies_to ?? ""),
        name: String(rule.name ?? ""),
        apply_on: String(rule.apply_on ?? "CIF"),
        notes: String(rule.notes ?? ""),
      }));
    },
    [],
  );

  const loadHistory = useCallback(
    async (page = 1) => {
      setHistoryLoading(true);
      setHistoryError(null);
      try {
        const params = new URLSearchParams({
          page: String(page),
          limit: "12",
        });
        if (historyStatus) {
          params.set("status", historyStatus);
        }
        const response = await apiClient.get<GazetteHistoryResponse>(
          `/gazette/history?${params.toString()}`,
        );
        setHistory(response.data);
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setHistoryError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load gazette history.",
          );
        } else {
          setHistoryError("Failed to load gazette history.");
        }
      } finally {
        setHistoryLoading(false);
      }
    },
    [historyStatus],
  );

  const loadGazetteDetail = useCallback(
    async (gazetteId: string) => {
      setDetailLoading(true);
      setDetailError(null);
      try {
        const response = await apiClient.get<GazetteDetailResponse>(
          `/gazette/${gazetteId}`,
        );
        setSelectedGazette(response.data);
        setDecisionSuccess(null);
        setDecisionError(null);
        setRejectionReason(response.data.rejection_reason ?? "");
        setEditableEffectiveDate(response.data.effective_date ?? "");
        setEditableRules(buildRuleDrafts(response.data.preview.rules));
      } catch (err: unknown) {
        if (isAxiosError(err)) {
          setDetailError(
            (err.response?.data as { detail?: string } | undefined)?.detail ??
              "Failed to load gazette details.",
          );
        } else {
          setDetailError("Failed to load gazette details.");
        }
      } finally {
        setDetailLoading(false);
      }
    },
    [buildRuleDrafts],
  );

  useEffect(() => {
    void loadHistory(1);
  }, [loadHistory, historyStatus]);

  const validateFile = (file: File) => {
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith(".pdf") && !lowerName.endsWith(".csv")) {
      return "Only PDF or CSV files are allowed.";
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return `File is too large. Max ${MAX_FILE_SIZE_MB}MB.`;
    }
    return null;
  };

  const selectedFileName = selectedFile?.name.toLowerCase() ?? "";
  const isGlobalTaxParametersCsv =
    selectedFileName === "global_tax_parameters.csv";
  const isHsCodeMatrixCsv = selectedFileName === "hs_code_matrix.csv";
  const isCatalogCsv = isGlobalTaxParametersCsv || isHsCodeMatrixCsv;
  const catalogPreviewColumns = catalogUploadResult?.preview_rows?.[0]
    ? Object.keys(catalogUploadResult.preview_rows[0]).filter(
        (column) => column !== "is_active",
      )
    : [];

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      setUploadError(error);
      setSelectedFile(null);
      return;
    }
    setUploadError(null);
    setSelectedFile(file);
  };

  const updateCatalogRowField = (
    rowIndex: number,
    field: string,
    value: string,
  ) => {
    setCatalogEditableRows((current) =>
      current.map((row, index) =>
        index === rowIndex
          ? {
              ...row,
              [field]: value,
            }
          : row,
      ),
    );
  };

  const saveCatalogRow = async (rowIndex: number) => {
    if (!catalogUploadResult) return;
    const row = catalogEditableRows[rowIndex];
    const rowId = String(row.id ?? "");
    if (!rowId) return;

    setCatalogSavingRowId(rowId);
    setUploadError(null);
    try {
      const response = await apiClient.patch<
        Record<string, string | number | boolean | null>
      >(`/gazette/catalog/${catalogUploadResult.dataset}/${rowId}`, {
        values: row,
        change_reason: catalogChangeReason.trim() || "Manual catalog edit",
      });

      setCatalogEditableRows((current) =>
        current.map((currentRow, index) =>
          index === rowIndex ? response.data : currentRow,
        ),
      );
      setCatalogUploadResult((current) =>
        current
          ? {
              ...current,
              preview_rows: current.preview_rows.map((currentRow, index) =>
                index === rowIndex ? response.data : currentRow,
              ),
            }
          : current,
      );
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setUploadError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to save catalog row.",
        );
      } else {
        setUploadError("Failed to save catalog row.");
      }
    } finally {
      setCatalogSavingRowId(null);
    }
  };

  const deleteCatalogRow = async (rowIndex: number) => {
    if (!catalogUploadResult) return;
    const row = catalogEditableRows[rowIndex];
    const rowId = String(row.id ?? "");
    if (!rowId) return;

    setCatalogDeletingRowId(rowId);
    setUploadError(null);
    try {
      await apiClient.delete(
        `/gazette/catalog/${catalogUploadResult.dataset}/${rowId}`,
        {
          params: {
            change_reason:
              catalogChangeReason.trim() || "Manual catalog deactivation",
          },
        },
      );

      setCatalogEditableRows((current) =>
        current.filter((_, index) => index !== rowIndex),
      );
      setCatalogUploadResult((current) =>
        current
          ? {
              ...current,
              preview_rows: current.preview_rows.filter(
                (_, index) => index !== rowIndex,
              ),
            }
          : current,
      );
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setUploadError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to deactivate catalog row.",
        );
      } else {
        setUploadError("Failed to deactivate catalog row.");
      }
    } finally {
      setCatalogDeletingRowId(null);
    }
  };

  const saveAllCatalogRows = async () => {
    if (!catalogUploadResult || catalogEditableRows.length === 0) return;
    setCatalogSavingAll(true);
    setUploadError(null);
    try {
      const nextRows: Record<string, string | number | boolean | null>[] = [];
      for (const row of catalogEditableRows) {
        const rowId = String(row.id ?? "");
        if (!rowId) {
          nextRows.push(row);
          continue;
        }
        const response = await apiClient.patch<
          Record<string, string | number | boolean | null>
        >(`/gazette/catalog/${catalogUploadResult.dataset}/${rowId}`, {
          values: row,
          change_reason:
            catalogChangeReason.trim() || "Manual catalog bulk edit",
        });
        nextRows.push(response.data);
      }

      setCatalogEditableRows(nextRows);
      setCatalogUploadResult((current) =>
        current
          ? {
              ...current,
              preview_rows: nextRows,
            }
          : current,
      );
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setUploadError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to save all catalog rows.",
        );
      } else {
        setUploadError("Failed to save all catalog rows.");
      }
    } finally {
      setCatalogSavingAll(false);
    }
  };

  const handleUpload = async () => {
    if (!isCatalogCsv && !gazetteNo.trim()) {
      setUploadError("Gazette number is required.");
      return;
    }
    if (!selectedFile) {
      setUploadError("Please select a PDF or CSV file.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setDecisionSuccess(null);
    setDecisionError(null);
    setUploadResult(null);
    setCatalogUploadResult(null);
    try {
      const form = new FormData();
      form.append("file", selectedFile);
      if (catalogEffectiveDate.trim()) {
        form.append("effective_date", catalogEffectiveDate.trim());
      }

      if (isGlobalTaxParametersCsv) {
        const response = await apiClient.post<CatalogUploadResponse>(
          "/gazette/upload-global-tax-parameters-csv",
          form,
          { headers: { "Content-Type": "multipart/form-data" } },
        );
        setCatalogUploadResult(response.data);
        setCatalogEditableRows(response.data.preview_rows);
      } else if (isHsCodeMatrixCsv) {
        const response = await apiClient.post<CatalogUploadResponse>(
          "/gazette/upload-hs-code-matrix-csv",
          form,
          { headers: { "Content-Type": "multipart/form-data" } },
        );
        setCatalogUploadResult(response.data);
        setCatalogEditableRows(response.data.preview_rows);
      } else {
        form.append("gazette_no", gazetteNo.trim());
        const uploadEndpoint = selectedFile.name.toLowerCase().endsWith(".csv")
          ? "/gazette/upload-csv"
          : "/gazette/upload";

        const response = await apiClient.post<GazetteUploadResponse>(
          uploadEndpoint,
          form,
          {
            headers: { "Content-Type": "multipart/form-data" },
          },
        );

        setUploadResult(response.data);
        setSelectedGazette({
          gazette_id: response.data.gazette_id,
          gazette_no: response.data.gazette_no,
          effective_date: response.data.effective_date,
          rules_count: response.data.rules_count,
          status: response.data.status,
          preview: response.data.preview,
          created_at: new Date().toISOString(),
        });
        setRejectionReason("");
        setEditableEffectiveDate(response.data.effective_date ?? "");
        setEditableRules(buildRuleDrafts(response.data.preview.rules));
      }

      setGazetteNo("");
      setCatalogEffectiveDate("");
      setCatalogChangeReason("");
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      await loadHistory(1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setUploadError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Upload failed.",
        );
      } else {
        setUploadError("Upload failed.");
      }
    } finally {
      setUploading(false);
    }
  };

  const updateRuleField = (
    index: number,
    field: keyof GazetteRuleDraft,
    value: string,
  ) => {
    setEditableRules((current) =>
      current.map((rule, ruleIndex) =>
        ruleIndex === index ? { ...rule, [field]: value } : rule,
      ),
    );
  };

  const addRule = () => {
    setEditableRules((current) => [...current, createEmptyRuleDraft()]);
  };

  const removeRule = (index: number) => {
    setEditableRules((current) =>
      current.filter((_, ruleIndex) => ruleIndex !== index),
    );
  };

  const saveReviewChanges = async () => {
    if (!selectedGazette) return;
    setDecisionError(null);
    setDecisionSuccess(null);
    setReviewSaving(true);
    try {
      const payload = {
        effective_date: editableEffectiveDate || null,
        rules: editableRules.map((rule) => ({
          rule_type: rule.rule_type.trim().toUpperCase(),
          vehicle_type: rule.vehicle_type.trim().toUpperCase(),
          fuel_type: rule.fuel_type.trim().toUpperCase(),
          category_code: rule.category_code.trim().toUpperCase() || null,
          hs_code: rule.hs_code.trim() || null,
          engine_min: Number(rule.engine_min || 0),
          engine_max: Number(rule.engine_max || 0),
          power_kw_min:
            rule.power_kw_min === "" ? null : Number(rule.power_kw_min),
          power_kw_max:
            rule.power_kw_max === "" ? null : Number(rule.power_kw_max),
          age_years_min:
            rule.age_years_min === "" ? null : Number(rule.age_years_min),
          age_years_max:
            rule.age_years_max === "" ? null : Number(rule.age_years_max),
          excise_type: rule.excise_type.trim().toUpperCase() || null,
          excise_rate:
            rule.excise_rate === "" ? null : Number(rule.excise_rate),
          customs_percent:
            rule.customs_percent === "" ? null : Number(rule.customs_percent),
          surcharge_percent:
            rule.surcharge_percent === ""
              ? null
              : Number(rule.surcharge_percent),
          excise_percent:
            rule.excise_percent === "" ? null : Number(rule.excise_percent),
          excise_per_kw_amount:
            rule.excise_per_kw_amount === ""
              ? null
              : Number(rule.excise_per_kw_amount),
          vat_percent:
            rule.vat_percent === "" ? null : Number(rule.vat_percent),
          pal_percent:
            rule.pal_percent === "" ? null : Number(rule.pal_percent),
          cess_percent:
            rule.cess_percent === "" ? null : Number(rule.cess_percent),
          cess_type: rule.cess_type.trim().toUpperCase() || null,
          cess_value: rule.cess_value === "" ? null : Number(rule.cess_value),
          luxury_tax_threshold:
            rule.luxury_tax_threshold === ""
              ? null
              : Number(rule.luxury_tax_threshold),
          luxury_tax_percent:
            rule.luxury_tax_percent === ""
              ? null
              : Number(rule.luxury_tax_percent),
          threshold_value:
            rule.threshold_value === "" ? null : Number(rule.threshold_value),
          rate_percent:
            rule.rate_percent === "" ? null : Number(rule.rate_percent),
          applies_to: rule.applies_to.trim().toUpperCase() || null,
          name: rule.name.trim() || null,
          apply_on: rule.apply_on.trim().toUpperCase(),
          notes: rule.notes.trim() || null,
        })),
      };
      const response = await apiClient.patch<GazetteDetailResponse>(
        `/gazette/${selectedGazette.gazette_id}`,
        payload,
      );
      setSelectedGazette(response.data);
      setEditableEffectiveDate(response.data.effective_date ?? "");
      setEditableRules(buildRuleDrafts(response.data.preview.rules));
      setDecisionSuccess("Gazette review changes saved.");
      await loadHistory(history?.page ?? 1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDecisionError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Failed to save review changes.",
        );
      } else {
        setDecisionError("Failed to save review changes.");
      }
    } finally {
      setReviewSaving(false);
    }
  };

  const approveGazette = async () => {
    if (!selectedGazette) return;
    setDecisionLoading(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      await apiClient.post(`/gazette/${selectedGazette.gazette_id}/approve`);
      setDecisionSuccess("Gazette approved. Tax rules activated.");
      setSelectedGazette((current) =>
        current
          ? {
              ...current,
              status: "APPROVED",
              rejection_reason: null,
            }
          : current,
      );
      await loadHistory(history?.page ?? 1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDecisionError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Approval failed.",
        );
      } else {
        setDecisionError("Approval failed.");
      }
    } finally {
      setDecisionLoading(false);
    }
  };

  const rejectGazette = async () => {
    if (!selectedGazette) return;
    const reason = rejectionReason.trim();
    if (reason.length < 10) {
      setDecisionError("Rejection reason must be at least 10 characters.");
      return;
    }
    setDecisionLoading(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      await apiClient.post(`/gazette/${selectedGazette.gazette_id}/reject`, {
        reason,
      });
      setDecisionSuccess("Gazette rejected. Reason saved.");
      setSelectedGazette((current) =>
        current
          ? {
              ...current,
              status: "REJECTED",
              rejection_reason: reason,
            }
          : current,
      );
      await loadHistory(history?.page ?? 1);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        setDecisionError(
          (err.response?.data as { detail?: string } | undefined)?.detail ??
            "Rejection failed.",
        );
      } else {
        setDecisionError("Rejection failed.");
      }
    } finally {
      setDecisionLoading(false);
    }
  };

  return (
    <div className="cd-container min-h-screen py-6 space-y-8">
      <header className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-orange-500">
              Gazette Control
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Gazette Upload, Review, and Approval
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Upload gazette PDFs, review extracted tax rules, and approve or
              reject with full audit coverage.
            </p>
          </div>
          <div className="rounded-2xl bg-slate-900 px-4 py-3 text-sm text-slate-100">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              Status
            </p>
            <p className="mt-1 text-lg font-semibold">
              {history?.total ?? 0} gazettes tracked
            </p>
          </div>
        </div>
      </header>

      <section id="upload" className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Upload Gazette File
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                PDF or CSV. Max {MAX_FILE_SIZE_MB}MB per file.
              </p>
            </div>
            <UploadCloud className="h-8 w-8 text-orange-400" />
          </div>

          <div className="mt-6 space-y-4">
            <label className="space-y-2 text-sm font-medium text-slate-700">
              Gazette Number
              <input
                value={gazetteNo}
                onChange={(event) => setGazetteNo(event.target.value)}
                placeholder="Example: 2026/03"
                disabled={isCatalogCsv}
                className="w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-orange-400 focus:outline-none"
              />
            </label>

            <label className="space-y-2 text-sm font-medium text-slate-700">
              Effective Date
              <input
                type="date"
                value={catalogEffectiveDate}
                onChange={(event) =>
                  setCatalogEffectiveDate(event.target.value)
                }
                className="w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-orange-400 focus:outline-none"
              />
            </label>

            <div
              onDragOver={(event) => {
                event.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragOver(false);
                const file = event.dataTransfer.files?.[0];
                if (file) handleFileSelect(file);
              }}
              onClick={() => inputRef.current?.click()}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed px-6 py-10 text-center transition",
                dragOver
                  ? "border-orange-400 bg-orange-500/10"
                  : "border-[#546a7b]/65 bg-[#c6c5b9]/20 hover:border-orange-300 hover:bg-orange-500/10",
              )}
            >
              <FileText className="h-10 w-10 text-gray-400" />
              <div className="text-sm text-gray-300">
                <p className="font-semibold text-white">
                  Drop PDF or CSV here or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  PDF uses extraction. Gazette CSV goes to review.
                  `global_tax_parameters.csv` and `hs_code_matrix.csv` import
                  directly.
                </p>
              </div>
              {selectedFile && (
                <div className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-[#393d3f]">
                  {selectedFile.name}
                </div>
              )}
            </div>

            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.csv,text/csv,application/pdf"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
            />

            {uploadError && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {uploadError}
              </div>
            )}

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-[#393d3f] transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {uploading ? "Uploading..." : "Upload for Review"}
            </button>

            {uploadResult?.message && (
              <div className="rounded-2xl border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-700">
                {uploadResult.message}
              </div>
            )}

            {catalogUploadResult?.message && (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {catalogUploadResult.message} Imported{" "}
                {catalogUploadResult.uploaded_rows} rows, superseded{" "}
                {catalogUploadResult.superseded_rows}.
              </div>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-[#546a7b]/65 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 text-slate-100 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            Latest Upload
          </p>
          {catalogUploadResult ? (
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Dataset</span>
                <span className="font-semibold text-white">
                  {catalogUploadResult.dataset}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Effective Date</span>
                <span className="font-semibold text-white">
                  {formatDate(catalogUploadResult.effective_date)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Rows Imported</span>
                <span className="font-semibold text-white">
                  {catalogUploadResult.uploaded_rows}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Rows Superseded</span>
                <span className="font-semibold text-white">
                  {catalogUploadResult.superseded_rows}
                </span>
              </div>
              <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-100">
                Catalog uploads activate directly after import. They do not
                create gazette review cards.
              </div>
            </div>
          ) : uploadResult ? (
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Gazette</span>
                <span className="font-semibold text-white">
                  {uploadResult.gazette_no}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Effective Date</span>
                <span className="font-semibold text-white">
                  {formatDate(uploadResult.effective_date)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Rules Extracted</span>
                <span className="font-semibold text-[#393d3f]">
                  {uploadResult.rules_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Confidence</span>
                <span className="font-semibold text-[#393d3f]">
                  {(uploadResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div>{statusBadge(uploadResult.status)}</div>
            </div>
          ) : (
            <div className="mt-4 text-sm text-slate-400">
              No uploads yet. Submit a gazette to generate previews.
            </div>
          )}
        </div>
      </section>

      <section
        id="review"
        className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Extracted Rules Review
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Validate the extracted rules before approval.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {selectedGazette && (
              <div className="rounded-2xl border border-[#546a7b]/65 px-3 py-2 text-sm text-[#546a7b]">
                Gazette{" "}
                <span className="font-semibold">
                  {selectedGazette.gazette_no}
                </span>
              </div>
            )}
            {selectedGazette && statusBadge(selectedGazette.status)}
          </div>
        </div>

        {detailLoading && (
          <div className="mt-6 text-sm text-slate-500">Loading gazette...</div>
        )}
        {detailError && (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {detailError}
          </div>
        )}

        {!selectedGazette && !detailLoading && !detailError && (
          <div className="mt-6 rounded-2xl border border-dashed border-slate-200 px-6 py-10 text-center text-sm text-slate-500">
            {catalogUploadResult
              ? "The latest action was a direct catalog import, so there is no gazette review card to approve."
              : "Select a gazette from history or upload a new one to review."}
          </div>
        )}

        {catalogUploadResult && !selectedGazette && (
          <div className="mt-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Dataset
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {catalogUploadResult.dataset}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Effective Date
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {formatDate(catalogUploadResult.effective_date)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Imported
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {catalogUploadResult.uploaded_rows}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Superseded
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {catalogUploadResult.superseded_rows}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              These rows were imported directly. You can edit or deactivate them
              here.
            </div>

            <label className="space-y-2 text-sm font-medium text-slate-700">
              Change Reason
              <input
                value={catalogChangeReason}
                onChange={(event) => setCatalogChangeReason(event.target.value)}
                placeholder="Reason for editing or deactivating a catalog row"
                className="w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-orange-400 focus:outline-none"
              />
            </label>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={saveAllCatalogRows}
                disabled={catalogSavingAll || catalogEditableRows.length === 0}
                className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {catalogSavingAll ? "Saving All..." : "Save All"}
              </button>
            </div>

            <div className="overflow-hidden rounded-2xl border border-white/10">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-white/10 text-sm">
                  <thead className="bg-white/5">
                    <tr>
                      {catalogPreviewColumns.map((column) => (
                        <th
                          key={column}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400"
                        >
                          {column.replaceAll("_", " ")}
                        </th>
                      ))}
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-400">
                        actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10 bg-white/0">
                    {catalogEditableRows.map((row, rowIndex) => (
                      <tr
                        key={`${catalogUploadResult.dataset}-row-${rowIndex}`}
                      >
                        {catalogPreviewColumns.map((column) => (
                          <td
                            key={`${rowIndex}-${column}`}
                            className="whitespace-nowrap px-4 py-3 text-white"
                          >
                            {column === "id" || column === "version" ? (
                              <span>
                                {row[column] === null ||
                                row[column] === undefined ||
                                row[column] === ""
                                  ? "—"
                                  : String(row[column])}
                              </span>
                            ) : (
                              <input
                                value={
                                  row[column] === null ||
                                  row[column] === undefined
                                    ? ""
                                    : String(row[column])
                                }
                                onChange={(event) =>
                                  updateCatalogRowField(
                                    rowIndex,
                                    column,
                                    event.target.value,
                                  )
                                }
                                className="w-full min-w-[120px] rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                              />
                            )}
                          </td>
                        ))}
                        <td className="px-4 py-3">
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => saveCatalogRow(rowIndex)}
                              disabled={catalogSavingRowId === String(row.id)}
                              className="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:bg-emerald-500 disabled:opacity-60"
                            >
                              {catalogSavingRowId === String(row.id)
                                ? "Saving"
                                : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteCatalogRow(rowIndex)}
                              disabled={catalogDeletingRowId === String(row.id)}
                              className="rounded-xl border border-rose-300 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-rose-600 transition hover:bg-rose-50 disabled:opacity-60"
                            >
                              {catalogDeletingRowId === String(row.id)
                                ? "Removing"
                                : "Remove"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedGazette && (
          <div className="mt-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Effective Date
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {formatDate(selectedGazette.effective_date)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Rules
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {selectedGazette.rules_count}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Uploaded
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {formatDateTime(selectedGazette.created_at)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-500">
                  Uploaded By
                </p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {selectedGazette.uploaded_by ?? "Unknown"}
                </p>
              </div>
            </div>

            <div className="space-y-4 rounded-2xl border border-white/10 p-4">
              <div className="grid gap-4 md:grid-cols-[220px_1fr]">
                <label className="space-y-2 text-sm font-medium text-slate-700">
                  Effective Date
                  <input
                    type="date"
                    value={editableEffectiveDate}
                    onChange={(event) =>
                      setEditableEffectiveDate(event.target.value)
                    }
                    className="w-full rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm text-white focus:border-orange-400 focus:outline-none"
                  />
                </label>
                <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                  Review the extracted values, correct any OCR mistakes, then
                  save before approval. The tax calculator will use the approved
                  rules from this review.
                </div>
              </div>

              {editableRules.length === 0 ? (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-700">
                  No structured rules were extracted. Add the rules manually,
                  save them, then approve the gazette.
                </div>
              ) : null}

              <div className="space-y-4">
                {editableRules.map((rule, index) => (
                  <div
                    key={`${selectedGazette.gazette_id}-rule-${index}`}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4"
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <p className="text-sm font-semibold text-white">
                        Rule {index + 1}
                      </p>
                      <button
                        type="button"
                        onClick={() => removeRule(index)}
                        className="rounded-xl border border-rose-300 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-rose-600 transition hover:bg-rose-50"
                      >
                        Remove
                      </button>
                    </div>

                    <div className="mb-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Rule Type
                        <select
                          value={rule.rule_type}
                          onChange={(event) => {
                            const nextType = event.target.value;
                            setEditableRules((current) =>
                              current.map((currentRule, ruleIndex) =>
                                ruleIndex === index
                                  ? {
                                      ...createEmptyRuleDraft(nextType),
                                      notes: currentRule.notes,
                                      hs_code: currentRule.hs_code,
                                    }
                                  : currentRule,
                              ),
                            );
                          }}
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        >
                          <option value="VEHICLE_TAX">VEHICLE_TAX</option>
                          <option value="CUSTOMS">CUSTOMS</option>
                          <option value="SURCHARGE">SURCHARGE</option>
                          <option value="LUXURY">LUXURY</option>
                        </select>
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        HS Code
                        <input
                          value={rule.hs_code}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "hs_code",
                              event.target.value,
                            )
                          }
                          placeholder="8703.80.31"
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Name
                        <input
                          value={rule.name}
                          onChange={(event) =>
                            updateRuleField(index, "name", event.target.value)
                          }
                          placeholder="CUSTOMS_SURCHARGE"
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Applies To
                        <input
                          value={rule.applies_to}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "applies_to",
                              event.target.value,
                            )
                          }
                          placeholder="CUSTOMS_DUTY"
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      {rule.rule_type === "VEHICLE_TAX" ? (
                        <>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Vehicle Type
                            <input
                              value={rule.vehicle_type}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "vehicle_type",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Fuel Type
                            <input
                              value={rule.fuel_type}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "fuel_type",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Category Code
                            <input
                              value={rule.category_code}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "category_code",
                                  event.target.value,
                                )
                              }
                              placeholder="PASSENGER_VEHICLE_BEV"
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Engine Min (cc)
                            <input
                              type="number"
                              value={rule.engine_min}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "engine_min",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Engine Max (cc)
                            <input
                              type="number"
                              value={rule.engine_max}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "engine_max",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Power Min (kW)
                            <input
                              type="number"
                              step="0.01"
                              value={rule.power_kw_min}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "power_kw_min",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Power Max (kW)
                            <input
                              type="number"
                              step="0.01"
                              value={rule.power_kw_max}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "power_kw_max",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Age Min (Years)
                            <input
                              type="number"
                              step="0.01"
                              value={rule.age_years_min}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "age_years_min",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Age Max (Years)
                            <input
                              type="number"
                              step="0.01"
                              value={rule.age_years_max}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "age_years_max",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Excise Type
                            <select
                              value={rule.excise_type}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "excise_type",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            >
                              <option value="">Select</option>
                              <option value="PER_KW">PER_KW</option>
                              <option value="PERCENTAGE">PERCENTAGE</option>
                            </select>
                          </label>
                          <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Excise Rate
                            <input
                              type="number"
                              step="0.01"
                              value={rule.excise_rate}
                              onChange={(event) =>
                                updateRuleField(
                                  index,
                                  "excise_rate",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                            />
                          </label>
                        </>
                      ) : null}
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Customs %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.customs_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "customs_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Surcharge %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.surcharge_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "surcharge_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Excise %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.excise_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "excise_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Excise Rs/kW
                        <input
                          type="number"
                          step="0.01"
                          value={rule.excise_per_kw_amount}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "excise_per_kw_amount",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        VAT %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.vat_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "vat_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        PAL %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.pal_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "pal_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        CESS %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.cess_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "cess_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        CESS Type
                        <select
                          value={rule.cess_type}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "cess_type",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        >
                          <option value="">Select</option>
                          <option value="PERCENT">PERCENT</option>
                          <option value="FIXED">FIXED</option>
                        </select>
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        CESS Value
                        <input
                          type="number"
                          step="0.01"
                          value={rule.cess_value}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "cess_value",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Threshold Value
                        <input
                          type="number"
                          step="0.01"
                          value={rule.threshold_value}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "threshold_value",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Rate %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.rate_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "rate_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Luxury Threshold
                        <input
                          type="number"
                          step="0.01"
                          value={rule.luxury_tax_threshold}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "luxury_tax_threshold",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Luxury Tax %
                        <input
                          type="number"
                          step="0.01"
                          value={rule.luxury_tax_percent}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "luxury_tax_percent",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Apply On
                        <select
                          value={rule.apply_on}
                          onChange={(event) =>
                            updateRuleField(
                              index,
                              "apply_on",
                              event.target.value,
                            )
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        >
                          <option value="CIF">CIF</option>
                          <option value="CIF_PLUS_CUSTOMS">
                            CIF_PLUS_CUSTOMS
                          </option>
                          <option value="CUSTOMS_ONLY">CUSTOMS_ONLY</option>
                          <option value="CIF_PLUS_EXCISE">
                            CIF_PLUS_EXCISE
                          </option>
                        </select>
                      </label>
                      <label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-gray-400 md:col-span-2 xl:col-span-2">
                        Notes
                        <input
                          value={rule.notes}
                          onChange={(event) =>
                            updateRuleField(index, "notes", event.target.value)
                          }
                          className="w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white focus:border-orange-400 focus:outline-none"
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={addRule}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50"
                >
                  Add Rule
                </button>
                <button
                  type="button"
                  onClick={saveReviewChanges}
                  disabled={reviewSaving}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {reviewSaving ? "Saving..." : "Save Review Changes"}
                </button>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-2xl border border-[#546a7b]/65 p-4">
                <label className="text-xs font-semibold uppercase tracking-wide text-[#546a7b]">
                  Rejection Reason
                </label>
                <textarea
                  value={rejectionReason}
                  onChange={(event) => setRejectionReason(event.target.value)}
                  placeholder="Provide a detailed reason if rejecting."
                  className="mt-2 min-h-[120px] w-full rounded-2xl border border-[#546a7b]/65 bg-transparent px-4 py-3 text-sm text-[#393d3f] focus:border-rose-400 focus:outline-none"
                />
                <p className="mt-2 text-xs text-[#546a7b]">
                  Minimum 10 characters required for rejection.
                </p>
              </div>
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={approveGazette}
                  disabled={
                    decisionLoading || selectedGazette.status === "APPROVED"
                  }
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-[#393d3f] transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Approve Gazette
                </button>
                <button
                  type="button"
                  onClick={rejectGazette}
                  disabled={
                    decisionLoading || selectedGazette.status === "REJECTED"
                  }
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-rose-600 px-4 py-3 text-sm font-semibold text-[#393d3f] transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <XCircle className="h-4 w-4" />
                  Reject Gazette
                </button>
                {decisionError && (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {decisionError}
                  </div>
                )}
                {decisionSuccess && (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                    {decisionSuccess}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>

      <section
        id="history"
        className="rounded-3xl border border-[#546a7b]/65 bg-[#c6c5b9]/20 p-6 shadow-sm"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Gazette History
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Track approvals and review pending gazettes.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-[#546a7b]">
              Status
              <select
                value={historyStatus}
                onChange={(event) => setHistoryStatus(event.target.value)}
                className="ml-2 rounded-xl border border-[#546a7b]/65 bg-transparent px-3 py-2 text-sm text-[#393d3f]"
              >
                <option value="">All</option>
                <option value="PENDING">PENDING</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
            </label>
            <button
              type="button"
              onClick={() => void loadHistory(1)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        {historyLoading ? (
          <div className="mt-6 text-sm text-slate-500">Loading history...</div>
        ) : historyError ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {historyError}
          </div>
        ) : !history || history.items.length === 0 ? (
          <div className="mt-6 rounded-2xl border border-dashed border-[#546a7b]/65 px-6 py-10 text-center text-sm text-[#546a7b]">
            No gazettes found for the selected filter.
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            <div className="overflow-x-auto rounded-2xl border border-[#546a7b]/65">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-[#c6c5b9]/20 text-xs uppercase tracking-wide text-[#546a7b]">
                  <tr>
                    <th className="px-4 py-3">Gazette</th>
                    <th className="px-4 py-3">Effective Date</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Rules</th>
                    <th className="px-4 py-3">Uploaded</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {history.items.map((item) => (
                    <tr key={item.id} className="hover:bg-[#c6c5b9]/20">
                      <td className="px-4 py-3 font-medium text-[#393d3f]">
                        {item.gazette_no}
                      </td>
                      <td className="px-4 py-3 text-[#546a7b]">
                        {formatDate(item.effective_date)}
                      </td>
                      <td className="px-4 py-3">{statusBadge(item.status)}</td>
                      <td className="px-4 py-3 text-[#546a7b]">
                        {item.rules_count}
                      </td>
                      <td className="px-4 py-3 text-[#546a7b]">
                        {formatDateTime(item.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => void loadGazetteDetail(item.id)}
                          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-xs font-semibold text-[#393d3f] transition hover:bg-slate-800"
                        >
                          <ClipboardCheck className="h-4 w-4" />
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-500">
                Page {history.page} of {history.total_pages}
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() =>
                    void loadHistory(Math.max(1, history.page - 1))
                  }
                  disabled={history.page <= 1}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() =>
                    void loadHistory(
                      Math.min(history.total_pages, history.page + 1),
                    )
                  }
                  disabled={history.page >= history.total_pages}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
