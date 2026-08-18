export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  timestamp: string;
}
