"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/authStore';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/?redirect=' + encodeURIComponent(window.location.pathname));
    } else if (user?.role && user.role !== 'admin') {
      if (user.role === 'student') router.replace('/student/dashboard');
      else if (user.role === 'faculty') router.replace('/faculty/dashboard');
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated || (user?.role && user.role !== 'admin')) return null;

  return <>{children}</>;
}
