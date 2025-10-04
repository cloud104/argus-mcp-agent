import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../auth/auth.service';
import { map } from 'rxjs/operators';

export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser$.pipe(
    map(user => {
      if (user && user.role === 'admin') {
        return true;
      }

      // Redirect to home if not admin
      router.navigate(['/']);
      return false;
    })
  );
};
