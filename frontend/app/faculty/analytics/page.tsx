"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";

interface TopQuestion {
  question: string;
  count: number;
}

interface WeakTopic {
  topic: string;
  count: number;
}

interface RecentQuestion {
  question: string;
  course_code: string;
  timestamp: string;
}

interface AnalyticsData {
  top_questions: TopQuestion[];
  questions_per_day: Record<string, number>;
  weak_topics: WeakTopic[];
  recent_questions: RecentQuestion[];
}

export default function FacultyAnalytics() {
  const [courseCode, setCourseCode] = useState("BAECE102");
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
        const res = await fetch(`${apiUrl}/analytics?course_code=${courseCode}`);
        if (!res.ok) throw new Error("Failed to fetch analytics");
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [courseCode]);

  const last7DaysChart = useMemo(() => {
    if (!data?.questions_per_day) return null;

    const days = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split("T")[0];
      days.push({
        date: dateStr,
        displayDate: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        count: data.questions_per_day[dateStr] || 0,
      });
    }

    const maxCount = Math.max(...days.map((d) => d.count), 5);
    const chartHeight = 150;
    const chartWidth = 400;
    const barWidth = 40;
    const gap = 15;

    return (
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
          Questions per Day (Last 7 Days)
        </h3>
        <div className="flex justify-center">
          <svg width={chartWidth} height={chartHeight + 30} className="overflow-visible">
            {days.map((day, i) => {
              const barHeight = (day.count / maxCount) * chartHeight;
              const x = i * (barWidth + gap) + 20;
              const y = chartHeight - barHeight;
              return (
                <g key={day.date}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={barHeight}
                    rx="4"
                    fill="#4f46e5"
                    className="transition-all duration-500 ease-out"
                  />
                  {day.count > 0 && (
                    <text
                      x={x + barWidth / 2}
                      y={y - 8}
                      textAnchor="middle"
                      className="text-[10px] font-bold fill-indigo-600"
                    >
                      {day.count}
                    </text>
                  )}
                  <text
                    x={x + barWidth / 2}
                    y={chartHeight + 20}
                    textAnchor="middle"
                    className="text-[10px] fill-slate-400 font-medium"
                  >
                    {day.displayDate}
                  </text>
                </g>
              );
            })}
            <line x1="0" y1={chartHeight} x2={chartWidth} y2={chartHeight} stroke="#e2e8f0" strokeWidth="1" />
          </svg>
        </div>
      </div>
    );
  }, [data]);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Faculty Analytics</h1>
            <p className="text-slate-500">Monitor student engagement and identified weak topics.</p>
          </div>
          <div className="flex items-center gap-3">
            <label htmlFor="course-select" className="text-sm font-medium text-slate-700">Course:</label>
            <input
              id="course-select"
              type="text"
              value={courseCode}
              onChange={(e) => setCourseCode(e.target.value)}
              className="bg-white border border-slate-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none w-32 font-semibold text-indigo-700"
              placeholder="Course Code"
            />
            <Link href="/" className="ml-4 text-sm text-indigo-600 font-medium hover:text-indigo-800 transition-colors">
              ← Back to Tutor
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
            Error: {error}
          </div>
        ) : !data ? (
          <div className="text-center py-12 text-slate-500">No data available for this course.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Top 10 Questions */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
              <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
                Top 10 Most Asked Questions
              </h3>
              <div className="space-y-3 flex-1">
                {data.top_questions.length > 0 ? (
                  data.top_questions.map((item, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100 group hover:border-indigo-200 transition-colors">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <p className="text-sm text-slate-700 flex-1 leading-snug">{item.question}</p>
                      <span className="px-2 py-1 rounded-md bg-white border border-slate-200 text-xs font-bold text-slate-500 group-hover:text-indigo-600 group-hover:border-indigo-100 shadow-sm">
                        {item.count}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 text-sm italic">No questions logged yet.</p>
                )}
              </div>
            </div>

            <div className="space-y-8">
              {/* Weak Topics Tag Cloud */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  Identified Weak Topics
                </h3>
                <div className="flex flex-wrap gap-3 items-center justify-center p-4">
                  {data.weak_topics.length > 0 ? (
                    data.weak_topics.map((wt, i) => {
                      const maxCount = Math.max(...data.weak_topics.map(t => t.count));
                      const minCount = Math.min(...data.weak_topics.map(t => t.count));
                      const fontSize = data.weak_topics.length > 1 && maxCount !== minCount
                        ? 12 + ((wt.count - minCount) / (maxCount - minCount)) * 12
                        : 16;
                      
                      return (
                        <span
                          key={i}
                          style={{ fontSize: `${fontSize}px` }}
                          className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg font-medium hover:bg-indigo-100 transition-colors cursor-default border border-indigo-100/50"
                        >
                          {wt.topic}
                        </span>
                      );
                    })
                  ) : (
                    <p className="text-slate-400 text-sm italic">No data to identify weak topics.</p>
                  )}
                </div>
              </div>

              {/* Bar Chart */}
              {last7DaysChart}
            </div>

            {/* Recent Questions Table */}
            <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-slate-100">
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Recent Questions
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 font-medium">
                      <th className="px-6 py-3">Question</th>
                      <th className="px-6 py-3 w-32">Course</th>
                      <th className="px-6 py-3 w-48">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.recent_questions.length > 0 ? (
                      data.recent_questions.map((q, i) => (
                        <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 text-slate-700 font-medium">{q.question}</td>
                          <td className="px-6 py-4">
                            <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-[10px] font-bold">
                              {q.course_code}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-slate-400 text-xs">
                            {new Date(q.timestamp).toLocaleString()}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="px-6 py-12 text-center text-slate-400 italic">
                          No recent activity.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
