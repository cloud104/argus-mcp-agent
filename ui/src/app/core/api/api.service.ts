import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timeout, catchError } from 'rxjs';
import { environment } from '../../../environments/environment';

// Types
export interface LogEntry {
  _id?: string;
  id?: string;
  timestamp: string;
  severity: string;
  appname: string;
  message: string;
  [key: string]: any;
}

export interface InitialAnalysisRequest {
  msg: string;
  index: string;
  window: string;
  session_id?: string;
}

export interface InitialAnalysisResponse {
  session_id: string;
  evidence_overview: {
    logs_encontrados: LogEntry[];
    [key: string]: any;
  };
}

export interface DeepDiveRequest {
  msg: string;
  index: string;
  session_id: string;
  tool_params: {
    logs: LogEntry[];
  };
}

export interface DeepDiveAnalysis {
  resumo_analitico: string;
  hipotese_causa_raiz: string;
  acoes_recomendadas: string[];
}

export interface DeepDiveResponse {
  answer: DeepDiveAnalysis;
  session_id: string;
}

export interface ChatRequest {
  user_input: string;
  session_id: string;
  initial_context?: {
    analysis: DeepDiveAnalysis;
    logs: LogEntry[];
  };
}

export interface ChatResponse {
  answer: string;
  session_id: string;
}

export interface LogExplanationRequest {
  log_line: string;
}

export interface LogExplanationResponse {
  explanation: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;
  private readonly DEFAULT_TIMEOUT = 30000; // 30 seconds
  private readonly DEEP_DIVE_TIMEOUT = 120000; // 2 minutes
  private readonly INITIAL_ANALYSIS_TIMEOUT = 120000; // 2 minutes

  constructor(private http: HttpClient) {}

  /**
   * Initial log analysis
   */
  initialAnalysis(request: InitialAnalysisRequest): Observable<InitialAnalysisResponse> {
    return this.http.post<InitialAnalysisResponse>(`${this.baseUrl}/initial-analysis`, request).pipe(
      timeout(this.INITIAL_ANALYSIS_TIMEOUT),
      catchError(this.handleError)
    );
  }

  /**
   * Deep dive analysis on filtered logs
   */
  deepDive(request: DeepDiveRequest): Observable<DeepDiveResponse> {
    return this.http.post<DeepDiveResponse>(`${this.baseUrl}/deep-dive`, request).pipe(
      timeout(this.DEEP_DIVE_TIMEOUT),
      catchError(this.handleError)
    );
  }

  /**
   * Chat with AI about analysis
   */
  chat(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, request).pipe(
      timeout(this.DEEP_DIVE_TIMEOUT),
      catchError(this.handleError)
    );
  }

  /**
   * Explain single log line
   */
  explainLogLine(request: LogExplanationRequest): Observable<LogExplanationResponse> {
    return this.http.post<LogExplanationResponse>(`${this.baseUrl}/explain-log-line`, request).pipe(
      timeout(this.DEFAULT_TIMEOUT),
      catchError(this.handleError)
    );
  }

  /**
   * Generic error handler
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'Ocorreu um erro desconhecido';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Erro: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.status === 0) {
        errorMessage = 'Não foi possível conectar ao servidor';
      } else if (error.status === 408) {
        errorMessage = 'A requisição excedeu o tempo limite';
      } else if (error.error?.detail) {
        errorMessage = error.error.detail;
      } else {
        errorMessage = `Erro do servidor: ${error.status} - ${error.statusText}`;
      }
    }

    console.error('API Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
