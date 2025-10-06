import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './change-password.component.html',
  styleUrl: './change-password.component.scss'
})
export class ChangePasswordComponent {
  form: FormGroup;
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);

  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router) {
    this.form = this.fb.group({
      oldPassword: ['', [Validators.required, Validators.minLength(8)]],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    const { oldPassword, newPassword } = this.form.value;
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.authService.changePassword(oldPassword, newPassword).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.successMessage.set('Senha alterada com sucesso!');
        setTimeout(() => this.router.navigate(['/']), 1000);
      },
      error: (error) => {
        const detail = error?.error?.detail;
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Erro ao alterar senha');
        this.isLoading.set(false);
      }
    });
  }
}


