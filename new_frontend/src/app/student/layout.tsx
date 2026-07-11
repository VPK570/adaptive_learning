"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/authStore';

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/');
    } else if (user?.role && user.role !== 'student') {
      if (user.role === 'faculty') router.replace('/faculty/dashboard');
      else if (user.role === 'admin') router.replace('/admin/dashboard');
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated || (user?.role && user.role !== 'student')) return null;

  return <>{children}</>;
}
