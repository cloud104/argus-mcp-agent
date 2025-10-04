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
      password: ['', [Validators.required, Validators.minLength(6)]],
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
        this.errorMessage.set(error.error?.detail || 'Erro ao criar usuário');
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
