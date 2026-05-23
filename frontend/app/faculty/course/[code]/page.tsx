"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

// --- Types ---

interface Course {
  code: string;
  name: string;
  description: string;
  icon: string;
}

interface Stats {
  total_chunks: number;
  text_chunks: number;
  image_chunks: number;
  documents?: { name: string; chunks: number }[];
}

interface FileStatus {
  name: string;
  status: "Idle" | "Uploading" | "Chunking documents" | "Generating embeddings" | "Course AI ready" | "Error";
  error?: string;
}

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
  out_of_scope: boolean;
}

interface AnalyticsData {
  top_questions: TopQuestion[];
  questions_per_day: Record<string, number>;
  weak_topics: WeakTopic[];
  recent_questions: RecentQuestion[];
}

// --- Components ---

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseCode = params.code as string;
  
  const [activeTab, setActiveTab] = useState<"materials" | "analytics" | "unanswered" | "coverage">("materials");
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        const res = await fetch(`${API_URL}/courses`);
        if (res.ok) {
          const courses: Course[] = await res.json();
          const match = courses.find(c => c.code === courseCode);
          setCourse(match || { code: courseCode, name: "Course Detail", description: "", icon: "📚" });
        }
      } catch (err) {
        console.error("Failed to fetch course:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCourse();
  }, [courseCode, API_URL]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{course?.icon}</span>
              <h1 className="text-3xl font-bold text-slate-900">{course?.name}</h1>
            </div>
            <p className="text-slate-500 font-mono">{courseCode}</p>
          </div>
          <div className="flex gap-3">
            <Link 
              href="/faculty"
              className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              ← All Courses
            </Link>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 mb-8 overflow-x-auto">
          {[
            { id: "materials", label: "Materials", icon: "📄" },
            { id: "analytics", label: "Analytics", icon: "📊" },
            { id: "unanswered", label: "Unanswered", icon: "❓" },
            { id: "coverage", label: "Coverage", icon: "🎯" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-4 text-sm font-medium whitespace-nowrap border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === "materials" && <MaterialsTab courseCode={courseCode} API_URL={API_URL} />}
          {activeTab === "analytics" && <AnalyticsTab courseCode={courseCode} API_URL={API_URL} />}
          {activeTab === "unanswered" && <UnansweredTab courseCode={courseCode} API_URL={API_URL} />}
          {activeTab === "coverage" && <CoverageTab courseCode={courseCode} API_URL={API_URL} />}
        </div>
      </div>
    </div>
  );
}

// --- Sub-Tabs ---

function MaterialsTab({ courseCode, API_URL }: { courseCode: string, API_URL: string }) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [curriculumFiles, setCurriculumFiles] = useState<string[]>([]);
  const [fileStatuses, setFileStatuses] = useState<FileStatus[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/stats?course_code=${courseCode}`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  }, [courseCode, API_URL]);

  const fetchCurriculum = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/curriculum?course=${courseCode}`);
      if (res.ok) {
        const data = await res.json();
        setCurriculumFiles(data);
      }
    } catch (err) {
      console.error("Failed to fetch curriculum:", err);
    }
  }, [courseCode, API_URL]);

  useEffect(() => {
    fetchStats();
    fetchCurriculum();
  }, [fetchStats, fetchCurriculum]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, isCurriculum: boolean = false) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles(filesArray);
      setFileStatuses(filesArray.map(f => ({ name: f.name, status: "Idle" })));
      // Note: for this simplified implementation, we use isCurriculum to decide where to POST
      // In a more robust UI, we'd have two separate upload inputs/states
    }
  };

  const uploadFile = async (file: File, isCurriculum: boolean = false) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("course_code", courseCode);

    updateFileStatus(file.name, "Uploading");

    try {
      const endpoint = isCurriculum ? `${API_URL}/curriculum` : `${API_URL}/ingest`;
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      updateFileStatus(file.name, "Course AI ready");
    } catch (err) {
      updateFileStatus(file.name, "Error", err instanceof Error ? err.message : String(err));
    }
  };
  
  const updateFileStatus = (name: string, status: FileStatus["status"], error?: string) => {
    setFileStatuses(prev => 
      prev.map(f => f.name === name ? { ...f, status, error } : f)
    );
  };

  const handleUpload = async (isCurriculum: boolean = false) => {
    if (selectedFiles.length === 0 || isUploading) return;

    setIsUploading(true);
    for (const file of selectedFiles) {
      await uploadFile(file, isCurriculum);
    }
    setIsUploading(false);
    if (isCurriculum) fetchCurriculum(); else fetchStats();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Regular Materials Upload */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Ingest Materials</h2>
            <div className="space-y-4">
              <label className="flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-xl hover:border-indigo-400 transition-colors bg-slate-50 cursor-pointer">
                <input type="file" multiple accept=".pdf" className="sr-only" onChange={(e) => handleFileChange(e)} />
                <span className="text-sm text-slate-600">Select PDF files</span>
              </label>
              <button
                onClick={() => handleUpload(false)}
                disabled={isUploading || selectedFiles.length === 0}
                className="w-full h-12 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 disabled:opacity-50"
              >
                Upload Materials
              </button>
            </div>
          </div>

          {/* Curriculum Upload */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border-2 border-indigo-200">
            <h2 className="text-lg font-semibold text-indigo-900 mb-4">Upload Curriculum</h2>
            <div className="space-y-4">
              <label className="flex justify-center px-6 pt-5 pb-6 border-2 border-indigo-300 border-dashed rounded-xl hover:border-indigo-400 transition-colors bg-indigo-50 cursor-pointer">
                <input type="file" multiple accept=".pdf" className="sr-only" onChange={(e) => handleFileChange(e, true)} />
                <span className="text-sm text-indigo-600">Select PDF files</span>
              </label>
              <button
                onClick={() => handleUpload(true)}
                disabled={isUploading || selectedFiles.length === 0}
                className="w-full h-12 bg-indigo-700 text-white font-semibold rounded-xl hover:bg-indigo-800 disabled:opacity-50"
              >
                Upload Curriculum
              </button>
            </div>
          </div>
        </div>

        {/* File List */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Files</h2>
          <div className="space-y-3">
             {curriculumFiles.map(file => (
               <div key={file} className="flex items-center justify-between p-3 rounded-lg bg-indigo-50 border border-indigo-100">
                 <span className="text-sm text-indigo-900 font-medium">{file}</span>
                 <span className="text-[10px] px-2 py-1 rounded bg-indigo-200 text-indigo-800 font-bold uppercase tracking-wider">Curriculum</span>
               </div>
             ))}
             {stats?.documents?.map(doc => (
               <div key={doc.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                 <span className="text-sm text-slate-700">{doc.name}</span>
                 <span className="text-[10px] px-2 py-1 rounded bg-slate-200 text-slate-700 font-bold uppercase tracking-wider">Material</span>
               </div>
             ))}
          </div>
        </div>
      </div>
      
      {/* ... stats display ... */}
    </div>
  );
}

function AnalyticsTab({ courseCode, API_URL }: { courseCode: string, API_URL: string }) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch(`${API_URL}/analytics?course_code=${courseCode}`);
        if (res.ok) setData(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [courseCode, API_URL]);

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
          Questions per Day
        </h3>
        <div className="flex justify-center">
          <svg width={chartWidth} height={chartHeight + 30} className="overflow-visible">
            {days.map((day, i) => {
              const barHeight = (day.count / maxCount) * chartHeight;
              const x = i * (barWidth + gap) + 20;
              const y = chartHeight - barHeight;
              return (
                <g key={day.date}>
                  <rect x={x} y={y} width={barWidth} height={barHeight} rx="4" fill="#4f46e5" />
                  {day.count > 0 && (
                    <text x={x + barWidth / 2} y={y - 8} textAnchor="middle" className="text-[10px] font-bold fill-indigo-600">{day.count}</text>
                  )}
                  <text x={x + barWidth / 2} y={chartHeight + 20} textAnchor="middle" className="text-[10px] fill-slate-400 font-medium">{day.displayDate}</text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    );
  }, [data]);

  if (loading) return <div className="text-center py-12">Loading analytics...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
          Top Questions
        </h3>
        <div className="space-y-3">
          {data?.top_questions.map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold flex items-center justify-center">{i + 1}</span>
              <p className="text-sm text-slate-700 flex-1">{item.question}</p>
              <span className="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-bold text-slate-500">{item.count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-8">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900 mb-6 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            Weak Topics
          </h3>
          <div className="flex flex-wrap gap-3 items-center justify-center p-4">
            {data?.weak_topics.map((wt, i) => {
              const maxCount = Math.max(...(data?.weak_topics.map(t => t.count) || [1]));
              const minCount = Math.min(...(data?.weak_topics.map(t => t.count) || [1]));
              const fontSize = 12 + ((wt.count - minCount) / (maxCount - minCount || 1)) * 12;
              return (
                <span key={i} style={{ fontSize: `${fontSize}px` }} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg font-medium border border-indigo-100/50">
                  {wt.topic}
                </span>
              );
            })}
          </div>
        </div>
        {last7DaysChart}
      </div>

      <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Recent Questions
          </h3>
        </div>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-slate-50 text-slate-500 font-medium">
              <th className="px-6 py-3">Question</th>
              <th className="px-6 py-3 w-48">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data?.recent_questions.map((q, i) => (
              <tr key={i} className="hover:bg-slate-50/50">
                <td className="px-6 py-4 text-slate-700">{q.question}</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{new Date(q.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function UnansweredTab({ courseCode, API_URL }: { courseCode: string, API_URL: string }) {
  const [questions, setQuestions] = useState<RecentQuestion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUnanswered = async () => {
      try {
        const res = await fetch(`${API_URL}/analytics/unanswered?course_code=${courseCode}`);
        if (res.ok) setQuestions(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchUnanswered();
  }, [courseCode, API_URL]);

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-amber-800 text-sm">
        These questions are outside your current course materials — consider uploading more content to cover these topics.
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-slate-50 text-slate-500 font-medium">
              <th className="px-6 py-3">Question</th>
              <th className="px-6 py-3 w-48">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {questions.length > 0 ? (
              questions.map((q, i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="px-6 py-4 text-slate-700 font-medium">{q.question}</td>
                  <td className="px-6 py-4 text-slate-400 text-xs">{new Date(q.timestamp).toLocaleString()}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={2} className="px-6 py-12 text-center text-slate-400 italic">No unanswered questions. Excellent coverage!</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CoverageTab({ courseCode, API_URL }: { courseCode: string, API_URL: string }) {
  const [coverage, setCoverage] = useState<Record<string, number>>({});
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [covRes, statsRes] = await Promise.all([
          fetch(`${API_URL}/analytics/coverage?course_code=${courseCode}`),
          fetch(`${API_URL}/stats?course_code=${courseCode}`)
        ]);
        if (covRes.ok) setCoverage(await covRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [courseCode, API_URL]);

  if (loading) return <div className="text-center py-12">Loading coverage...</div>;

  const docs = stats?.documents || [];
  const maxHits = Math.max(...Object.values(coverage), 5);

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold text-slate-900 mb-6">Material Coverage</h3>
      <div className="space-y-6">
        {docs.length > 0 ? (
          docs.map((doc, i) => {
            const hits = coverage[doc.name] || 0;
            const percentage = (hits / maxHits) * 100;
            const isUnused = hits === 0;

            return (
              <div key={i} className="space-y-2">
                <div className="flex justify-between items-end">
                  <div className="overflow-hidden">
                    <p className={`text-sm font-medium truncate ${isUnused ? "text-red-500" : "text-slate-700"}`}>
                      {doc.name} {isUnused && "(Not being studied)"}
                    </p>
                    <p className="text-xs text-slate-400">{doc.chunks} chunks</p>
                  </div>
                  <p className={`text-sm font-bold ${isUnused ? "text-red-500" : "text-indigo-600"}`}>{hits} hits</p>
                </div>
                <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                  <div 
                    className={`h-full transition-all duration-1000 ease-out ${isUnused ? "bg-red-400" : "bg-indigo-500"}`}
                    style={{ width: `${Math.max(percentage, isUnused ? 2 : 5)}%` }}
                  />
                </div>
              </div>
            );
          })
        ) : (
          <p className="text-center text-slate-400 italic py-12">No documents found for this course.</p>
        )}
      </div>
    </div>
  );
}
