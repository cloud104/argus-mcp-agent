import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { UserAdminService, User, CreateUserRequest } from '../../../core/services/user-admin.service';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './user-management.component.html',
  styleUrl: './user-management.component.scss'
})
export class UserManagementComponent implements OnInit {
  users = signal<User[]>([]);
  isLoading = signal(false);
  showCreateModal = signal(false);
  showResetModal = signal(false);
  showEmailModal = signal(false);
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);

  createUserForm: FormGroup;

  constructor(
    private userAdminService: UserAdminService,
    private fb: FormBuilder,
    private router: Router
  ) {
    this.createUserForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      role: ['viewer', Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadUsers();
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  loadUsers(): void {
    this.isLoading.set(true);
    this.userAdminService.getUsers().subscribe({
      next: (users) => {
        this.users.set(users);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.errorMessage.set(error.message || 'Erro ao carregar usuários');
        this.isLoading.set(false);
      }
    });
  }

  openCreateModal(): void {
    this.showCreateModal.set(true);
    this.createUserForm.reset({ role: 'viewer' });
    this.errorMessage.set(null);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
    this.createUserForm.reset();
  }

  // Reset password modal state
  selectedUserForReset: User | null = null;
  selectedUserForEmail: User | null = null;

  openResetModal(user: User): void {
    this.selectedUserForReset = user;
    this.showResetModal.set(true);
  }

  closeResetModal(): void {
    this.selectedUserForReset = null;
    this.showResetModal.set(false);
  }

  openEmailModal(user: User): void {
    this.selectedUserForEmail = user;
    this.showEmailModal.set(true);
  }

  closeEmailModal(): void {
    this.selectedUserForEmail = null;
    this.showEmailModal.set(false);
  }

  onResetPassword(newPassword: string): void {
    if (!this.selectedUserForReset) return;
    if (!newPassword || newPassword.length < 8) {
      this.errorMessage.set('Senha deve ter no mínimo 8 caracteres');
      return;
    }

    this.isLoading.set(true);
    this.userAdminService.resetUserPassword(this.selectedUserForReset.username, newPassword).subscribe({
      next: () => {
        this.successMessage.set('Senha atualizada com sucesso!');
        this.isLoading.set(false);
        this.closeResetModal();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        const detail = error?.error?.detail;
        const message = typeof detail === 'string' ? detail : (error?.message || 'Erro ao atualizar senha');
        this.errorMessage.set(message);
        this.isLoading.set(false);
      }
    });
  }

  onUpdateEmail(newEmail: string): void {
    if (!this.selectedUserForEmail) return;
    if (!newEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
      this.errorMessage.set('Email inválido');
      return;
    }

    this.isLoading.set(true);
    this.userAdminService.updateUserEmail(this.selectedUserForEmail.username, newEmail).subscribe({
      next: () => {
        this.successMessage.set('Email atualizado com sucesso!');
        this.isLoading.set(false);
        this.closeEmailModal();
        this.loadUsers();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        const detail = error?.error?.detail;
        const message = typeof detail === 'string' ? detail : (error?.message || 'Erro ao atualizar email');
        this.errorMessage.set(message);
        this.isLoading.set(false);
      }
    });
  }

  onCreateUser(): void {
    if (this.createUserForm.invalid) return;

    const userData: CreateUserRequest = this.createUserForm.value;
    this.isLoading.set(true);

    this.userAdminService.createUser(userData).subscribe({
      next: (response) => {
        this.successMessage.set(`Usuário ${response.username} criado com sucesso!`);
        this.closeCreateModal();
        this.loadUsers();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        // Extrai mensagens de erro retornadas pelo FastAPI (por vezes como array de objetos)
        const detail = error?.error?.detail;
        let message = 'Erro ao criar usuário';
        if (typeof detail === 'string') {
          message = detail;
        } else if (Array.isArray(detail)) {
          message = detail
            .map((d: any) => d?.msg || d?.detail || JSON.stringify(d))
            .join(' | ');
        } else if (detail?.message) {
          message = detail.message;
        } else if (error?.message) {
          message = error.message;
        }
        this.errorMessage.set(message);
        this.isLoading.set(false);
      }
    });
  }

  toggleUserStatus(user: User): void {
    const action = user.disabled ? 'enable' : 'disable';
    const service = user.disabled
      ? this.userAdminService.enableUser(user.username)
      : this.userAdminService.disableUser(user.username);

    service.subscribe({
      next: () => {
        this.successMessage.set(`Usuário ${action === 'enable' ? 'ativado' : 'desativado'} com sucesso!`);
        this.loadUsers();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || `Erro ao ${action === 'enable' ? 'ativar' : 'desativar'} usuário`);
      }
    });
  }

  updateUserRole(user: User, newRole: 'admin' | 'viewer'): void {
    if (user.role === newRole) return;

    this.userAdminService.updateUserRole(user.username, newRole).subscribe({
      next: () => {
        this.successMessage.set('Role atualizado com sucesso!');
        this.loadUsers();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || 'Erro ao atualizar role');
      }
    });
  }

  deleteUser(user: User): void {
    if (!confirm(`Tem certeza que deseja excluir o usuário ${user.username}?`)) {
      return;
    }

    this.userAdminService.deleteUser(user.username).subscribe({
      next: () => {
        this.successMessage.set('Usuário excluído com sucesso!');
        this.loadUsers();
        setTimeout(() => this.successMessage.set(null), 3000);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.detail || 'Erro ao excluir usuário');
      }
    });
  }

  getRoleBadgeClass(role: string): string {
    return role === 'admin' ? 'badge-admin' : 'badge-viewer';
  }

  getStatusBadgeClass(disabled: boolean): string {
    return disabled ? 'badge-disabled' : 'badge-active';
  }
}
