import { Component, OnInit, AfterViewInit, OnDestroy, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { AuthService, User } from '../../core/auth/auth.service';
import { ApiService, LogEntry, InitialAnalysisResponse } from '../../core/api/api.service';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
Chart.register(...registerables);

interface FilterPill {
  value: string;
  label: string;
}

@Component({
  selector: 'app-log-explorer',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ScrollingModule],
  templateUrl: './log-explorer.component.html',
  styleUrl: './log-explorer.component.scss'
})
export class LogExplorerComponent implements OnInit, OnDestroy {
  searchForm: FormGroup;
  currentUser!: Observable<User | null>;
  logHistogramChart: Chart | null = null;

  // State signals
  isSearching = signal(false);
  isDeepDiving = signal(false);
  isExplaining = signal(false);
  isChatting = signal(false);
  allLogs = signal<LogEntry[]>([]);
  filterPills = signal<FilterPill[]>([]);
  sessionId = signal<string>('');
  currentIndex = signal<string>('');
  currentWindow = signal<string>('');
  errorMessage = signal<string | null>(null);
  showInsightsPanel = signal(false);
  deepDiveAnalysis = signal<any>(null);
  expandedLogIndex = signal<number>(-1);
  logExplanation = signal<string>('');
  showChat = signal(false);
  chatMessages = signal<Array<{text: string, sender: 'user' | 'ai'}>>([]);
  showExportMenu = signal(false);

  // Pagination signals
  currentPage = signal(1);
  itemsPerPage = signal(50);
  itemsPerPageOptions = [25, 50, 100, 200];

  // Computed
  filteredLogs = computed(() => {
    const logs = this.allLogs();
    const pills = this.filterPills();

    if (pills.length === 0) return logs;

    return logs.filter(log => {
      return pills.every(pill => {
        const pillValue = pill.value.toLowerCase();

        // Check if it's a field:value filter
        if (pillValue.includes(':')) {
          const [key, value] = pillValue.split(':', 2);
          const logValue = (log as any)[key];
          return logValue && String(logValue).toLowerCase().includes(value);
        }

        // Otherwise search in entire log object
        return JSON.stringify(log).toLowerCase().includes(pillValue);
      });
    });
  });

  // Quick filters computed from logs
  quickFilters = computed(() => {
    const logs = this.allLogs();
    if (logs.length === 0) return { severities: [], appnames: [], hosts: [] };

    const severities = new Set<string>();
    const appnames = new Map<string, number>();
    const hosts = new Map<string, number>();

    logs.forEach(log => {
      if (log.severity) severities.add(log.severity);
      if (log.appname) {
        appnames.set(log.appname, (appnames.get(log.appname) || 0) + 1);
      }
      if (log['host']) {
        const shortHost = log['host'].split('(')[0]; // Extract short hostname
        hosts.set(shortHost, (hosts.get(shortHost) || 0) + 1);
      }
    });

    return {
      severities: Array.from(severities).sort(),
      appnames: Array.from(appnames.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([name]) => name),
      hosts: Array.from(hosts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([name]) => name)
    };
  });

  // Pagination computed
  totalPages = computed(() => {
    const total = this.filteredLogs().length;
    const perPage = this.itemsPerPage();
    return Math.ceil(total / perPage) || 1;
  });

  paginatedLogs = computed(() => {
    const logs = this.filteredLogs();
    const page = this.currentPage();
    const perPage = this.itemsPerPage();
    const start = (page - 1) * perPage;
    const end = start + perPage;
    return logs.slice(start, end);
  });

  paginationInfo = computed(() => {
    const total = this.filteredLogs().length;
    const page = this.currentPage();
    const perPage = this.itemsPerPage();
    const start = total === 0 ? 0 : (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, total);
    return { start, end, total };
  });

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private apiService: ApiService,
    private router: Router
  ) {
    // Initialize form with default values
    // Use last 7 days as default range
    const now = new Date();
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    this.searchForm = this.fb.group({
      ccode: ['csalva7', [Validators.required]],
      topology: ['203089', [Validators.required]],
      startDate: [sevenDaysAgo.toISOString().slice(0, 16), [Validators.required]],
      endDate: [now.toISOString().slice(0, 16), [Validators.required]]
    });

    // Update chart when filtered logs change
    effect(() => {
      const logs = this.filteredLogs();
      if (logs.length > 0) {
        setTimeout(() => this.renderLogHistogram(), 100);
      }
    });
  }

  ngOnInit(): void {
    // Initialize currentUser observable
    this.currentUser = this.authService.currentUser$;

    // Check if user is authenticated
    if (!this.authService.hasToken()) {
      this.router.navigate(['/login']);
    }
  }

  onSearch(): void {
    if (this.searchForm.invalid) {
      return;
    }

    const { ccode, topology, startDate, endDate } = this.searchForm.value;
    const index = `${ccode}_${topology}_logs`;

    // Calculate time window from date range
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end.getTime() - start.getTime();
    const diffHours = Math.ceil(diffMs / (1000 * 60 * 60));
    const window = `${Math.max(1, diffHours)}h`;

    this.currentIndex.set(index);
    this.currentWindow.set(window);

    this.isSearching.set(true);
    this.errorMessage.set(null);

    const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

    this.apiService.initialAnalysis({
      msg: 'Análise inicial',
      index,
      window,
      session_id: sessionId
    }).subscribe({
      next: (response: InitialAnalysisResponse) => {
        this.sessionId.set(response.session_id);

        const logs = response.evidence_overview?.logs_encontrados || [];

        // Enrich logs with severity if missing
        const enrichedLogs = logs.map(log => {
          if (!log.severity) {
            const msgLower = (log.message || '').toLowerCase();
            if (msgLower.includes('error') || msgLower.includes('fatal') || msgLower.includes('critical')) {
              log.severity = 'ERROR';
            } else if (msgLower.includes('warn')) {
              log.severity = 'WARNING';
            } else {
              log.severity = 'INFO';
            }
          }

          // Extract appname from message if not present
          if (!log.appname) {
            const match = (log.message || '').match(/\[([^\]]+)\]/);
            log.appname = match ? match[1] : 'unknown';
          }

          return log;
        });

        this.allLogs.set(enrichedLogs);
        this.isSearching.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.message || 'Erro ao buscar logs');
        this.isSearching.set(false);
      }
    });
  }

  addFilter(event: KeyboardEvent): void {
    if (event.key !== 'Enter') return;

    const input = event.target as HTMLInputElement;
    const value = input.value.trim();

    if (value && !this.filterPills().some(p => p.value === value)) {
      this.filterPills.update(pills => [...pills, { value, label: value }]);
      input.value = '';
    }
  }

  removeFilter(index: number): void {
    this.filterPills.update(pills => pills.filter((_, i) => i !== index));
  }

  clearAllFilters(): void {
    this.filterPills.set([]);
  }

  toggleInsightsPanel(): void {
    this.showInsightsPanel.update(v => !v);
  }

  /**
   * Perform deep dive analysis on currently filtered logs
   */
  onDeepDive(): void {
    const logs = this.filteredLogs();

    if (logs.length === 0) {
      this.errorMessage.set('Nenhum log disponível para análise');
      return;
    }

    this.isDeepDiving.set(true);
    this.errorMessage.set(null);

    this.apiService.deepDive({
      msg: 'Deep dive analysis',
      index: this.currentIndex(),
      session_id: this.sessionId(),
      tool_params: {
        logs
      }
    }).subscribe({
      next: (response) => {
        // Store the full analysis object
        this.deepDiveAnalysis.set(response.answer);
        this.showInsightsPanel.set(true);
        this.isDeepDiving.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.message || 'Erro ao realizar análise profunda');
        this.isDeepDiving.set(false);
      }
    });
  }

  /**
   * Explain a single log line (with inline expansion)
   */
  onExplainLog(logLine: string, index: number): void {
    if (!logLine) return;

    // If clicking the same log, collapse it
    if (this.expandedLogIndex() === index) {
      this.expandedLogIndex.set(-1);
      this.logExplanation.set('');
      return;
    }

    this.expandedLogIndex.set(index);
    this.logExplanation.set(''); // Clear previous
    this.isExplaining.set(true);
    this.errorMessage.set(null);

    this.apiService.explainLogLine({
      log_line: logLine
    }).subscribe({
      next: (response) => {
        this.logExplanation.set(response.explanation);
        this.isExplaining.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.message || 'Erro ao explicar log');
        this.isExplaining.set(false);
        this.expandedLogIndex.set(-1);
      }
    });
  }

  /**
   * Start chat interface
   */
  startChat(): void {
    this.showChat.set(true);
    this.chatMessages.set([]);
    // Collapse analysis sections but keep them visible
  }

  /**
   * Send chat message
   */
  sendChatMessage(message: string): void {
    if (!message.trim()) return;

    // Add user message to chat
    this.chatMessages.update(msgs => [...msgs, { text: message, sender: 'user' }]);

    this.isChatting.set(true);

    const isFirstMessage = this.chatMessages().length === 1;

    this.apiService.chat({
      user_input: message,
      session_id: this.sessionId(),
      initial_context: isFirstMessage ? {
        analysis: this.deepDiveAnalysis(),
        logs: this.filteredLogs()
      } : undefined
    }).subscribe({
      next: (response) => {
        this.chatMessages.update(msgs => [...msgs, { text: response.answer, sender: 'ai' }]);
        this.isChatting.set(false);
      },
      error: (error) => {
        this.chatMessages.update(msgs => [...msgs, { text: `Erro: ${error.message}`, sender: 'ai' }]);
        this.isChatting.set(false);
      }
    });
  }

  /**
   * Handle chat keydown event
   */
  onChatKeydown(event: KeyboardEvent, textarea: HTMLTextAreaElement): void {
    if (!event.shiftKey && textarea.value.trim()) {
      event.preventDefault();
      this.sendChatMessage(textarea.value);
      textarea.value = '';
    }
  }

  /**
   * Handle chat submit button click
   */
  onChatSubmit(textarea: HTMLTextAreaElement): void {
    if (textarea.value.trim()) {
      this.sendChatMessage(textarea.value);
      textarea.value = '';
    }
  }

  logout(): void {
    this.authService.logout();
  }

  navigateToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin/users']);
  }

  /**
   * Pagination methods
   */
  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
      // Scroll to top of logs list
      const logsContainer = document.querySelector('.logs-list');
      if (logsContainer) {
        logsContainer.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  }

  nextPage(): void {
    this.goToPage(this.currentPage() + 1);
  }

  previousPage(): void {
    this.goToPage(this.currentPage() - 1);
  }

  changeItemsPerPage(items: number): void {
    this.itemsPerPage.set(items);
    this.currentPage.set(1); // Reset to first page
  }

  getPageNumbers(): number[] {
    const total = this.totalPages();
    const current = this.currentPage();
    const delta = 2; // Pages to show on each side of current

    const range: number[] = [];
    const rangeWithDots: number[] = [];

    for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
      range.push(i);
    }

    if (current - delta > 2) {
      rangeWithDots.push(1, -1); // -1 represents "..."
    } else {
      rangeWithDots.push(1);
    }

    rangeWithDots.push(...range);

    if (current + delta < total - 1) {
      rangeWithDots.push(-1, total);
    } else if (total > 1) {
      rangeWithDots.push(total);
    }

    return rangeWithDots;
  }

  /**
   * TrackBy function for virtual scrolling
   */
  trackByLogId(index: number, log: LogEntry): any {
    return log._id || log.id || index;
  }

  /**
   * Copy text to clipboard
   */
  copyToClipboard(text: string, event: Event): void {
    event.preventDefault();
    event.stopPropagation();

    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
      // Add visual feedback
      const button = (event.currentTarget as HTMLElement);
      button.classList.add('copied');

      setTimeout(() => {
        button.classList.remove('copied');
      }, 2000);
    }).catch(err => {
      console.error('Erro ao copiar texto:', err);
    });
  }

  getSeverityClass(severity: string): string {
    const sev = severity?.toUpperCase();
    if (['EMERG', 'ERROR', 'FATAL', 'CRITICAL'].includes(sev)) return 'severity-error';
    if (sev === 'WARNING') return 'severity-warning';
    return 'severity-info';
  }

  /**
   * Toggle quick filter (add or remove)
   */
  toggleQuickFilter(field: string, value: string): void {
    const filterValue = `${field}:${value}`;
    const currentPills = this.filterPills();
    const existingIndex = currentPills.findIndex(p => p.value === filterValue);

    if (existingIndex >= 0) {
      // Remove filter
      this.filterPills.set(currentPills.filter((_, i) => i !== existingIndex));
    } else {
      // Add filter
      this.filterPills.set([...currentPills, { value: filterValue, label: `${field}: ${value}` }]);
    }
  }

  /**
   * Check if quick filter is active
   */
  isFilterActive(field: string, value: string): boolean {
    const filterValue = `${field}:${value}`;
    return this.filterPills().some(p => p.value === filterValue);
  }

  /**
   * Toggle export menu
   */
  toggleExportMenu(): void {
    this.showExportMenu.update(v => !v);
  }

  /**
   * Export analysis to file
   */
  exportAnalysis(format: 'markdown' | 'json'): void {
    const analysis = this.deepDiveAnalysis();
    const logs = this.filteredLogs();
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `argus-analysis-${this.currentIndex()}-${timestamp}`;

    let content: string;
    let mimeType: string;
    let extension: string;

    if (format === 'markdown') {
      content = this.generateMarkdown(analysis, logs);
      mimeType = 'text/markdown';
      extension = 'md';
    } else {
      content = JSON.stringify({
        metadata: {
          index: this.currentIndex(),
          window: this.currentWindow(),
          timestamp: new Date().toISOString(),
          totalLogs: logs.length
        },
        analysis,
        logs: logs.slice(0, 50) // Include first 50 logs
      }, null, 2);
      mimeType = 'application/json';
      extension = 'json';
    }

    // Create and download file
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.${extension}`;
    link.click();
    window.URL.revokeObjectURL(url);

    this.showExportMenu.set(false);
  }

  /**
   * Generate Markdown from analysis
   */
  private generateMarkdown(analysis: any, logs: any[]): string {
    const timestamp = new Date().toISOString();
    let md = `# Argus Log Analysis Report\n\n`;
    md += `**Date:** ${timestamp}\n`;
    md += `**Index:** ${this.currentIndex()}\n`;
    md += `**Window:** ${this.currentWindow()}\n`;
    md += `**Total Logs:** ${logs.length}\n\n`;
    md += `---\n\n`;

    if (analysis.resumo_analitico) {
      md += `## 📋 Resumo Analítico\n\n${analysis.resumo_analitico}\n\n`;
    }

    if (analysis.hipotese_causa_raiz) {
      md += `## 🔍 Hipótese de Causa Raiz\n\n${analysis.hipotese_causa_raiz}\n\n`;
    }

    if (analysis.acoes_recomendadas && analysis.acoes_recomendadas.length > 0) {
      md += `## ✅ Ações Recomendadas\n\n`;
      analysis.acoes_recomendadas.forEach((action: string, i: number) => {
        md += `${i + 1}. ${action}\n`;
      });
      md += `\n`;
    }

    // Add sample logs
    md += `## 📊 Amostra de Logs (primeiros 10)\n\n`;
    logs.slice(0, 10).forEach((log, i) => {
      md += `### Log ${i + 1}\n`;
      md += `- **Timestamp:** ${log.timestamp}\n`;
      md += `- **Severity:** ${log.severity}\n`;
      md += `- **Appname:** ${log.appname}\n`;
      md += `- **Message:** ${log.message}\n\n`;
    });

    md += `---\n\n`;
    md += `*Gerado por Argus Log Explorer*\n`;

    return md;
  }

  /**
   * Render log histogram chart
   */
  renderLogHistogram(): void {
    const canvas = document.getElementById('logHistogram') as HTMLCanvasElement;
    if (!canvas) return;

    const logs = this.filteredLogs();
    if (logs.length === 0) return;

    // Destroy existing chart
    if (this.logHistogramChart) {
      this.logHistogramChart.destroy();
      this.logHistogramChart = null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Group logs by severity
    const severities = ['EMERG', 'ERROR', 'FATAL', 'CRITICAL', 'WARNING', 'INFO'];
    const colors: { [key: string]: string } = {
      'EMERG': 'rgba(220, 38, 38, 0.7)',
      'ERROR': 'rgba(220, 38, 38, 0.7)',
      'FATAL': 'rgba(220, 38, 38, 0.7)',
      'CRITICAL': 'rgba(220, 38, 38, 0.7)',
      'WARNING': 'rgba(245, 158, 11, 0.7)',
      'INFO': 'rgba(59, 130, 246, 0.7)'
    };

    const datasets = severities.map(sev => ({
      label: sev,
      data: logs
        .filter(l => l.severity && l.severity.toUpperCase() === sev)
        .map(l => ({
          x: new Date(l.timestamp).valueOf(),
          y: 1
        })),
      backgroundColor: colors[sev],
      borderColor: colors[sev],
      borderWidth: 1
    })).filter(ds => ds.data.length > 0);

    const config: ChartConfiguration = {
      type: 'bar',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'minute',
              displayFormats: {
                minute: 'HH:mm'
              }
            },
            stacked: true,
            grid: {
              display: false
            },
            ticks: {
              color: '#64748b'
            }
          },
          y: {
            stacked: true,
            beginAtZero: true,
            grid: {
              color: '#e2e8f0'
            },
            ticks: {
              color: '#64748b',
              precision: 0
            }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 20,
              color: '#1e293b'
            }
          },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false
          }
        }
      }
    };

    this.logHistogramChart = new Chart(ctx, config);
  }

  ngOnDestroy(): void {
    // Cleanup chart
    if (this.logHistogramChart) {
      this.logHistogramChart.destroy();
    }
  }
}
