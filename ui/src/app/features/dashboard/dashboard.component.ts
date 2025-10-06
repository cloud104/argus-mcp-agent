import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MetricsService, DashboardMetrics } from '../../core/services/metrics.service';
import { AuthService } from '../../core/auth/auth.service';
import { Observable } from 'rxjs';
import { User } from '../../core/auth/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  metrics = signal<DashboardMetrics | null>(null);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  selectedWindow = signal('7d');
  currentUser: Observable<User | null>;

  windows = [
    { label: '24 Horas', value: '24h' },
    { label: '7 Dias', value: '7d' },
    { label: '30 Dias', value: '30d' },
    { label: 'Custom', value: 'custom' }
  ];

  constructor(
    private metricsService: MetricsService,
    private router: Router,
    private authService: AuthService
  ) {
    this.currentUser = this.authService.currentUser$;
  }

  ngOnInit(): void {
    this.loadMetrics();
  }

  loadMetrics(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    // Para simplificar, se custom o back pode receber start/end via query params mais tarde
    this.metricsService.getDashboardMetrics('csalva7_203089_logs', this.selectedWindow()).subscribe({
      next: (data) => {
        this.metrics.set(data);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || 'Erro ao carregar métricas');
        this.isLoading.set(false);
      }
    });
  }

  applyCustomRange(start: string, end: string): void {
    if (!start || !end) {
      this.errorMessage.set('Selecione início e fim do intervalo');
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    // Converte para ISO completo (YYYY-MM-DDTHH:mm)
    const startIso = new Date(start).toISOString();
    const endIso = new Date(end).toISOString();

    this.metricsService.getDashboardMetricsRange('csalva7_203089_logs', startIso, endIso).subscribe({
      next: (data) => {
        this.metrics.set(data);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || 'Erro ao carregar métricas');
        this.isLoading.set(false);
      }
    });
  }

  changeWindow(window: string): void {
    this.selectedWindow.set(window);
    this.loadMetrics();
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  logout(): void {
    this.authService.logout();
  }

  goToChangePassword(): void {
    this.router.navigate(['/change-password']);
  }

  getSeverityKeys(): string[] {
    const dist = this.metrics()?.severity_distribution;
    return dist ? Object.keys(dist).sort() : [];
  }

  getAppnameKeys(): string[] {
    const dist = this.metrics()?.appname_distribution;
    return dist ? Object.keys(dist).sort((a, b) => (dist[b] || 0) - (dist[a] || 0)).slice(0, 5) : [];
  }

  formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  getSeverityColor(severity: string): string {
    const colors: { [key: string]: string } = {
      'error': '#ef4444',
      'warning': '#f59e0b',
      'info': '#3b82f6',
      'debug': '#6b7280',
      'notice': '#8b5cf6',
      'alert': '#dc2626',
      'critical': '#991b1b'
    };
    return colors[severity.toLowerCase()] || '#6b7280';
  }

  getErrorRateColor(): string {
    const rate = this.metrics()?.error_rate || 0;
    if (rate > 20) return '#ef4444';
    if (rate > 10) return '#f59e0b';
    return '#10b981';
  }
}
