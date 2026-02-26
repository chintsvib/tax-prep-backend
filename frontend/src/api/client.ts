import type {
  AuthRequest,
  TokenResponse,
  RefundExplainerRequest,
  RefundExplainerResponse,
  LifeEventPreset,
  LifeEventApplyRequest,
  LifeEventApplyResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(
      body?.detail || `Request failed: ${res.status} ${res.statusText}`
    );
  }

  return res.json();
}

// --- Auth ---

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function signup(
  email: string,
  password: string,
  full_name: string
): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name } as AuthRequest),
  });
}

// --- Refund Explainer ---

export async function explainRefundChange(
  data: RefundExplainerRequest
): Promise<RefundExplainerResponse> {
  return request<RefundExplainerResponse>("/insights/explain-refund-change", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// --- Life Events ---

export async function getLifeEvents(): Promise<LifeEventPreset[]> {
  return request<LifeEventPreset[]>("/life-events");
}

export async function applyLifeEvent(
  data: LifeEventApplyRequest
): Promise<LifeEventApplyResponse> {
  return request<LifeEventApplyResponse>("/life-events/apply", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
