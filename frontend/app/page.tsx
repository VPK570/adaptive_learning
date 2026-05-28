"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Course {
  course_code: string;
  course_name: string;
  doc_count: number;
  chunk_count: number;
}

interface Question {
  keywords: string[];
}

export default function Dashboard() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [enrolledCourses, setEnrolledCourses] = useState<Record<string, boolean>>({});
  const [lastQuestions, setLastQuestions] = useState<Record<string, string>>({});
  const [progressData, setProgressData] = useState<Record<string, { covered: number; weak: number }>>({});
  const router = useRouter();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  const fetchProgress = useCallback(async (code: string) => {
    try {
      const res = await fetch(`${API_URL}/questions?course_code=${code}`);
      if (res.ok) {
        const questions: Question[] = await res.json();
        const keywordCounts: Record<string, number> = {};
        questions.forEach(q => {
          if (q && q.keywords) {
            q.keywords.forEach(kw => {
              keywordCounts[kw] = (keywordCounts[kw] || 0) + 1;
            });
          }
        });

        let covered = 0;
        let weak = 0;
        Object.values(keywordCounts).forEach(count => {
          if (count >= 2) covered++;
          else if (count === 1) weak++;
        });

        setProgressData(prev => ({
          ...prev,
          [code]: { covered, weak }
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch progress for ${code}:`, error);
    }
  }, [API_URL]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/courses`);
        if (res.ok) {
          const data = await res.json();
          setCourses(data);
          
          // Load enrolled status and last questions from localStorage
          const enrolled: Record<string, boolean> = {};
          const lasts: Record<string, string> = {};
          data.forEach((course: Course) => {
            enrolled[course.course_code] = localStorage.getItem(`enrolled_${course.course_code}`) === "true";
            lasts[course.course_code] = localStorage.getItem(`last_question_${course.course_code}`) || "";
            fetchProgress(course.course_code);
          });
          setEnrolledCourses(enrolled);
          setLastQuestions(lasts);
        }
      } catch (error) {
        console.error("Failed to fetch courses:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [API_URL, fetchProgress]);

  const toggleEnroll = (e: React.MouseEvent, code: string) => {
    e.stopPropagation();
    const newState = !enrolledCourses[code];
    setEnrolledCourses(prev => ({ ...prev, [code]: newState }));
    localStorage.setItem(`enrolled_${code}`, String(newState));
  };

  const getProgressRing = (code: string) => {
    const data = progressData[code];
    if (!data || (data.covered === 0 && data.weak === 0)) {
      return (
        <svg width="40" height="40" viewBox="0 0 40 40" className="transform -rotate-90">
          <circle cx="20" cy="20" r="16" fill="transparent" stroke="#e2e8f0" strokeWidth="4" />
        </svg>
      );
    }

    const total = data.covered + data.weak;
    const percentage = (data.covered / total) * 100;
    const circumference = 2 * Math.PI * 16;
    const offset = circumference - (percentage / 100) * circumference;

    return (
      <svg width="40" height="40" viewBox="0 0 40 40" className="transform -rotate-90">
        <circle cx="20" cy="20" r="16" fill="transparent" stroke="#e2e8f0" strokeWidth="4" />
        <circle
          cx="20"
          cy="20"
          r="16"
          fill="transparent"
          stroke="#4f46e5"
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10">
          <h1 className="text-3xl font-bold text-slate-900">Student Dashboard</h1>
          <p className="text-slate-500 mt-2">Welcome back! Continue your learning journey.</p>
        </header>

        {courses.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-slate-200">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-semibold text-slate-800">No courses available yet</h2>
            <p className="text-slate-500 mt-2">Check back later or contact your faculty.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <div
                key={course.course_code}
                onClick={() => router.push(`/chat?course=${course.course_code}`)}
                className={`group bg-white rounded-2xl p-6 shadow-sm border-2 transition-all cursor-pointer hover:shadow-md ${
                  enrolledCourses[course.course_code] ? "border-indigo-600" : "border-transparent"
                }`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center text-xl font-bold">
                    {course.course_code.substring(0, 1)}
                  </div>
                  <div className="flex items-center gap-3">
                    {getProgressRing(course.course_code)}
                    <button
                      onClick={(e) => toggleEnroll(e, course.course_code)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        enrolledCourses[course.course_code]
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {enrolledCourses[course.course_code] ? "Enrolled" : "Enroll"}
                    </button>
                  </div>
                </div>

                <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  {course.course_name}
                </h3>
                <p className="text-sm font-mono text-slate-500 mb-4">{course.course_code}</p>

                <div className="flex gap-4 mb-6">
                  <div className="text-xs text-slate-400">
                    <span className="font-semibold text-slate-600">{course.doc_count}</span> Documents
                  </div>
                  <div className="text-xs text-slate-400">
                    <span className="font-semibold text-slate-600">{course.chunk_count}</span> Chunks
                  </div>
                </div>

                {lastQuestions[course.course_code] && (
                  <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-100">
                    <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Continue where you left off</p>
                    <p className="text-xs text-slate-600 italic line-clamp-2">
                      "{lastQuestions[course.course_code].substring(0, 60)}..."
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
