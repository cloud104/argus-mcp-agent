import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface DashboardMetrics {
  total_logs: number;
  severity_distribution: { [key: string]: number };
  appname_distribution: { [key: string]: number };
  top_hosts: Array<{ host: string; count: number }>;
  hourly_distribution: Array<{ timestamp: string; count: number }>;
  error_rate: number;
  window: string;
  period: {
    start: string;
    end: string;
  };
  coverage_days: number;
}

@Injectable({
  providedIn: 'root'
})
export class MetricsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Get dashboard metrics
   */
  getDashboardMetrics(index: string = 'csalva7_203089_logs', window: string = '7d'): Observable<DashboardMetrics> {
    return this.http.get<DashboardMetrics>(`${this.apiUrl}/metrics/dashboard`, {
      params: { index, window }
    });
  }

  /**
   * Get dashboard metrics with explicit start/end (ISO 8601)
   */
  getDashboardMetricsRange(index: string, start: string, end: string): Observable<DashboardMetrics> {
    return this.http.get<DashboardMetrics>(`${this.apiUrl}/metrics/dashboard`, {
      params: { index, start, end }
    });
  }
}
