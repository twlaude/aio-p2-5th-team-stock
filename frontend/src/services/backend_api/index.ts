import type { ApiMode, BackendApiClient } from "./client";
import { createLiveClient } from "./live";
import { mockApiClient } from "./mock";

export const apiMode: ApiMode = import.meta.env.VITE_API_MODE === "live" ? "live" : "mock";

export const apiClient: BackendApiClient = apiMode === "live" ? createLiveClient() : mockApiClient;

export type * from "./client";
