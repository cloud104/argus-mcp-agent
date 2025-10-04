import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: '',
    loadComponent: () => import('./features/log-explorer/log-explorer.component').then(m => m.LogExplorerComponent),
    canActivate: [authGuard]
  },
  {
    path: 'admin/users',
    loadComponent: () => import('./features/admin/user-management/user-management.component').then(m => m.UserManagementComponent),
    canActivate: [authGuard, adminGuard]
  },
  {
    path: '**',
    redirectTo: ''
  }
];
