"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const STUDENT_LINKS = [
  { href: "/", label: "Courses" },
  { href: "/progress", label: "My Progress" },
  { href: "/flashcards", label: "Flashcards" },
  { href: "/quiz", label: "Quiz" },
];

const FACULTY_LINKS = [
  { href: "/faculty", label: "My Courses" },
  { href: "/faculty/generate", label: "Generate Paper" },
];

export default function Navbar() {
  const pathname = usePathname();

  const renderLink = (link: { href: string; label: string }) => {
    const isActive = pathname === link.href;
    return (
      <Link
        key={link.href}
        href={link.href}
        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? "text-indigo-600 bg-indigo-50"
            : "text-slate-600 hover:text-indigo-600 hover:bg-slate-50"
        }`}
      >
        {link.label}
      </Link>
    );
  };

  return (
    <nav className="sticky top-0 z-50 w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
                AI
              </div>
              <span className="font-bold text-slate-900 hidden sm:block">Adaptive Tutor</span>
            </div>
            
            <div className="hidden md:flex md:items-center md:space-x-1">
              <div className="flex space-x-1">
                {STUDENT_LINKS.map(renderLink)}
              </div>
              
              <div className="h-6 w-px bg-slate-200 mx-2" aria-hidden="true" />
              
              <div className="flex space-x-1">
                {FACULTY_LINKS.map(renderLink)}
              </div>
            </div>
          </div>
          
          {/* Mobile menu button (simplified) */}
          <div className="flex items-center md:hidden">
            <select 
              className="text-sm border-slate-200 rounded-lg p-1"
              value={pathname}
              onChange={(e) => window.location.href = e.target.value}
            >
              <optgroup label="Student">
                {STUDENT_LINKS.map(link => (
                  <option key={link.href} value={link.href}>{link.label}</option>
                ))}
              </optgroup>
              <optgroup label="Faculty">
                {FACULTY_LINKS.map(link => (
                  <option key={link.href} value={link.href}>{link.label}</option>
                ))}
              </optgroup>
            </select>
          </div>
        </div>
      </div>
    </nav>
  );
}
