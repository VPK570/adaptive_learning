"use client";

import { useState, useEffect, useCallback, useMemo } from "react";

interface QuestionLog {
  question: string;
  course_code: string;
  timestamp: string;
  response_preview: string;
}

const STOP_WORDS = new Set([
  "what", "is", "the", "a", "an", "of", "and", "in", "to", "for", "how", "why", "on", 
  "can", "you", "tell", "me", "about", "with", "from", "that", "this", "these", "those",
  "where", "when", "who", "which", "are", "was", "were", "been", "being", "have", "has", 
  "had", "does", "do", "did", "but", "not", "if", "or", "as", "at", "by", "for", "with",
  "about", "against", "between", "into", "through", "during", "before", "after", "above",
  "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
  "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
  "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
  "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
]);

interface Course {
  course_code: string;
  course_name: string;
  icon: string;
}

export default function StudentProgress() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseCode, setCourseCode] = useState("");
  const [questions, setQuestions] = useState<QuestionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  useEffect(() => {
    async function fetchCourses() {
      try {
        const res = await fetch(`${API_URL}/courses`);
        if (!res.ok) throw new Error("Failed to fetch courses");
        const data: Course[] = await res.json();
        setCourses(data);

        // Find default course: first one where localStorage key `enrolled_{code}` is true
        const defaultCourse = data.find(c => localStorage.getItem(`enrolled_${c.course_code}`) === "true") || data[0];
        if (defaultCourse) setCourseCode(defaultCourse.course_code);
      } catch (err) {
        console.error("Error fetching courses:", err);
      }
    }
    fetchCourses();
  }, [API_URL]);

  const fetchQuestions = useCallback(async () => {
    if (!courseCode) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/questions?course_code=${courseCode}`);
      if (res.ok) {
        const data = await res.json();
        setQuestions(data);
      } else {
        throw new Error("Failed to fetch questions");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }, [courseCode, API_URL]);

  useEffect(() => {
    if (courseCode) fetchQuestions();
  }, [fetchQuestions, courseCode]);

  const [topics, setTopics] = useState<{weak_areas: string[], suggested_revision: string[]}>({weak_areas: [], suggested_revision: []});

  useEffect(() => {
    async function fetchAnalytics() {
      if (!courseCode) return;
      setLoading(true);
      try {
        const [analyticsRes, topicsRes] = await Promise.all([
          fetch(`${API_URL}/analytics?course_code=${courseCode}`),
          fetch(`${API_URL}/curriculum/topics?course=${courseCode}`)
        ]);
        
        const analytics = await analyticsRes.json();
        const topicsList = await topicsRes.json();
        
        setQuestions(analytics.recent_questions);
        setTopics({
          weak_areas: analytics.weak_topics,
          suggested_revision: analytics.suggested_revision
        });
      } catch (err) {
        setError("Failed to load analytics");
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, [courseCode, API_URL]);

  const groupedHistory = useMemo(() => {
    const groups: Record<string, QuestionLog[]> = {};
    questions.forEach(q => {
      const date = new Date(q.timestamp).toLocaleDateString(undefined, { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
      if (!groups[date]) groups[date] = [];
      groups[date].push(q);
    });
    // Sort keys by date descending
    return Object.entries(groups).sort((a, b) => {
      return new Date(b[1][0].timestamp).getTime() - new Date(a[1][0].timestamp).getTime();
    });
  }, [questions]);

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12 font-sans">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 md:flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Learning Progress</h1>
            <p className="text-slate-500">Track your journey through the course material</p>
          </div>
          <div className="mt-4 md:mt-0 flex items-center gap-3">
            <select
              value={courseCode}
              onChange={(e) => setCourseCode(e.target.value)}
              className="px-4 py-2 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-sans text-sm bg-white"
            >
              {courses.map(c => (
                <option key={c.course_code} value={c.course_code}>
                  {c.icon} {c.course_name} ({c.course_code})
                </option>
              ))}
            </select>
            <a 
              href="/"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              ← Chat
            </a>
          </div>
        </div>

        {loading ? (
          <div className="py-20 text-center">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-500">Analyzing your progress...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
            <p className="text-red-600">⚠️ {error}</p>
            <button onClick={fetchQuestions} className="mt-4 text-sm font-semibold text-red-700 underline">Try again</button>
          </div>
        ) : questions.length === 0 ? (
          <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 shadow-sm">
            <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">
              🎓
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">No session history found</h2>
            <p className="text-slate-500 mb-8 max-w-sm mx-auto">
              Start a conversation with the AI Tutor to see your learning analytics here.
            </p>
            <a 
              href="/"
              className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100"
            >
              Start Learning
            </a>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Top Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Weak Areas</h2>
                <div className="flex flex-wrap gap-2">
                  {topics.weak_areas.length > 0 ? (
                    topics.weak_areas.map((topic, i) => (
                      <span key={i} className="px-3 py-1.5 bg-amber-50 text-amber-700 border border-amber-100 rounded-full text-sm font-medium">
                        {topic}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400 italic">Looking strong! No weak areas found.</p>
                  )}
                </div>
              </div>
              
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
                 <p className="text-sm text-slate-500 mb-2">Need detailed tracking?</p>
                 <a href="/faculty/generate" className="text-sm font-semibold text-indigo-600 underline">Upload Curriculum PDF</a>
              </div>
            </div>

            {/* Suggested Revision */}
            {topics.suggested_revision.length > 0 && (
              <div className="bg-indigo-600 rounded-2xl p-6 shadow-lg shadow-indigo-100 text-white">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center text-xl shrink-0">
                    💡
                  </div>
                  <div>
                    <h2 className="text-lg font-bold mb-1">Suggested Revision</h2>
                    <p className="text-indigo-100 text-sm mb-4 leading-relaxed">
                      Based on your curriculum, these topics haven't been explored yet:
                    </p>
                    <ul className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {topics.suggested_revision.slice(0, 6).map((topic, i) => (
                        <li key={i} className="text-xs bg-white/10 px-3 py-1 rounded-lg border border-white/20">
                          • {topic}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Session History */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">Session History</h2>
                <span className="text-xs font-medium text-slate-500">{questions.length} questions total</span>
              </div>
              <div className="divide-y divide-slate-100">
                {groupedHistory.map(([date, items]) => (
                  <div key={date} className="px-6 py-6">
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-4 sticky top-0 bg-white/80 backdrop-blur-sm py-1">
                      {date}
                    </h3>
                    <div className="space-y-6">
                      {items.map((q, i) => (
                        <div key={i} className="relative pl-6 before:absolute before:left-0 before:top-2 before:bottom-0 before:w-px before:bg-indigo-100">
                          <div className="absolute left-[-4px] top-1.5 w-2 h-2 rounded-full bg-indigo-400 ring-4 ring-white" />
                          <p className="text-sm font-semibold text-slate-800 mb-1">{q.question}</p>
                          <p className="text-xs text-slate-500 line-clamp-2 italic leading-relaxed">
                            "{q.response_preview}..."
                          </p>
                          <div className="mt-2 text-[10px] text-slate-400 font-mono">
                            {new Date(q.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
