"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/authStore';

export default function FacultyLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/');
    } else if (user?.role && user.role !== 'faculty') {
      if (user.role === 'student') router.replace('/student/dashboard');
      else if (user.role === 'admin') router.replace('/admin/dashboard');
    }
  }, [isAuthenticated, user]);

  if (!isAuthenticated || (user?.role && user.role !== 'faculty')) return null;

  return <>{children}</>;
}
