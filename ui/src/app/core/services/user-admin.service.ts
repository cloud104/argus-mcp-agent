import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  username: string;
  email: string;
  role: 'admin' | 'viewer';
  disabled: boolean;
  created_at: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: 'admin' | 'viewer';
}

export interface UpdateRoleRequest {
  role: 'admin' | 'viewer';
}

export interface ResetPasswordRequest {
  new_password: string;
}

export interface UpdateEmailRequest {
  new_email: string;
}

@Injectable({
  providedIn: 'root'
})
export class UserAdminService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Get all users
   */
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/auth/users`);
  }

  /**
   * Create new user
   */
  createUser(user: CreateUserRequest): Observable<{ message: string; username: string }> {
    return this.http.post<{ message: string; username: string }>(
      `${this.apiUrl}/auth/users`,
      user
    );
  }

  /**
   * Update user role
   */
  updateUserRole(username: string, role: 'admin' | 'viewer'): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}/role`,
      { role }
    );
  }

  /**
   * Reset user password (admin)
   */
  resetUserPassword(username: string, newPassword: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}/password`,
      { new_password: newPassword }
    );
  }

  /**
   * Update user email (admin)
   */
  updateUserEmail(username: string, newEmail: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}/email`,
      { new_email: newEmail }
    );
  }

  /**
   * Disable user
   */
  disableUser(username: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}/disable`,
      {}
    );
  }

  /**
   * Enable user
   */
  enableUser(username: string): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}/enable`,
      {}
    );
  }

  /**
   * Delete user
   */
  deleteUser(username: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${this.apiUrl}/auth/users/${username}`
    );
  }
}
