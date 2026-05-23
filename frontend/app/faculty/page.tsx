"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

interface Course {
  course_code: string;
  course_name: string;
  description: string;
  icon: string;
  created_at: string;
  doc_count?: number;
  chunk_count?: number;
}

const EMOJI_OPTIONS = ["📚", "🔬", "💻", "🧮", "⚡", "🧬", "📐", "🎯"];

export default function FacultyDashboard() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [newCourse, setNewCourse] = useState({
    course_code: "",
    course_name: "",
    description: "",
    icon: "📚",
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  const fetchCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/courses`);
      if (res.ok) {
        const data = await res.json();
        setCourses(data);
      } else {
        // Fallback to empty list if endpoint doesn't exist yet
        console.warn("GET /courses failed or not implemented");
        setCourses([]);
      }
    } catch (err) {
      console.error("Failed to fetch courses:", err);
      setError("Failed to connect to the backend server.");
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/courses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newCourse),
      });

      if (res.ok) {
        setIsModalOpen(false);
        setNewCourse({ course_code: "", course_name: "", description: "", icon: "📚" });
        fetchCourses();
      } else {
        const data = await res.json();
        alert(data.detail || "Failed to create course");
      }
    } catch (err) {
      console.error("Create course error:", err);
      alert("Failed to create course. Please try again.");
    }
  };

  const handleDeleteCourse = async (course_code: string) => {
    if (!window.confirm(`Are you sure you want to delete course ${course_code}?`)) return;

    try {
      const res = await fetch(`${API_URL}/courses/${course_code}`, {
        method: "DELETE",
      });

      if (res.ok) {
        fetchCourses();
      } else {
        alert("Failed to delete course");
      }
    } catch (err) {
      console.error("Delete course error:", err);
      alert("Failed to delete course");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12 font-sans">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">My Courses</h1>
            <p className="text-slate-500 mt-1">Manage your academic courses and knowledge bases</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center justify-center px-5 py-2.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 gap-2"
          >
            <span className="text-xl">+</span> Create Course
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* Course Grid */}
        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
          </div>
        ) : courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <div
                key={course.course_code}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col h-full"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-2xl shadow-inner border border-indigo-100">
                    {course.icon}
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest bg-indigo-50 px-2 py-1 rounded-md border border-indigo-100">
                      {course.course_code}
                    </span>
                  </div>
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-2">{course.course_name}</h3>
                <p className="text-slate-500 text-sm line-clamp-2 mb-6 flex-grow">
                  {course.description || "No description provided."}
                </p>

                <div className="grid grid-cols-2 gap-4 mb-6 border-y border-slate-50 py-4">
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Documents</p>
                    <p className="text-lg font-bold text-slate-700">{course.doc_count ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Chunks</p>
                    <p className="text-lg font-bold text-slate-700">{course.chunk_count ?? 0}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-auto pt-2">
                  <span className="text-xs text-slate-400">
                    Created {new Date(course.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDeleteCourse(course.course_code)}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Course"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                    <Link
                      href={`/faculty/course/${course.course_code}`}
                      className="px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-xl hover:bg-slate-800 transition-colors"
                    >
                      Open
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300">
            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 text-4xl">
              📂
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">No courses yet</h3>
            <p className="text-slate-500 mb-8 max-w-sm mx-auto">
              Get started by creating your first course. You'll then be able to upload documents and train your AI.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center justify-center px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100"
            >
              + Create Your First Course
            </button>
          </div>
        )}

        {/* Create Course Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
              <div className="px-8 pt-8 pb-4">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-slate-900">Create Course</h2>
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </button>
                </div>

                <form onSubmit={handleCreateCourse} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                      Course Code
                    </label>
                    <input
                      required
                      type="text"
                      value={newCourse.course_code}
                      onChange={(e) => setNewCourse({ ...newCourse, course_code: e.target.value.toUpperCase() })}
                      placeholder="e.g. CS101"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                      Course Name
                    </label>
                    <input
                      required
                      type="text"
                      value={newCourse.course_name}
                      onChange={(e) => setNewCourse({ ...newCourse, course_name: e.target.value })}
                      placeholder="e.g. Introduction to Computer Science"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                      Description
                    </label>
                    <textarea
                      rows={3}
                      value={newCourse.description}
                      onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                      placeholder="What is this course about?"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold text-slate-700 mb-2 uppercase tracking-wider">
                      Choose Icon
                    </label>
                    <div className="grid grid-cols-4 gap-3">
                      {EMOJI_OPTIONS.map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => setNewCourse({ ...newCourse, icon: emoji })}
                          className={`h-12 flex items-center justify-center text-xl rounded-xl border-2 transition-all ${
                            newCourse.icon === emoji
                              ? "border-indigo-600 bg-indigo-50 scale-105 shadow-sm"
                              : "border-slate-100 bg-slate-50 hover:border-slate-200"
                          }`}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 pb-8">
                    <button
                      type="submit"
                      className="w-full py-4 bg-indigo-600 text-white font-bold rounded-2xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 active:scale-[0.98]"
                    >
                      Create Course
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
