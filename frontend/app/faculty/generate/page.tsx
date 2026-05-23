"use client";

import { useState, useRef } from "react";
import Link from "next/link";

interface Question {
  number: number;
  text: string;
  marks: number;
  options?: string[];
}

interface PaperSection {
  title: string;
  questions: Question[];
}

interface GeneratedPaper {
  course_code: string;
  total_marks: number;
  difficulty: string;
  sections: PaperSection[];
}

export default function GeneratePaper() {
  const [courseCode, setCourseCode] = useState("BAECE102");
  const [totalMarks, setTotalMarks] = useState(50);
  const [difficulty, setDifficulty] = useState("Medium");
  const [topicInput, setTopicInput] = useState("");
  const [topics, setTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [paper, setPaper] = useState<GeneratedPaper | null>(null);
  const [error, setError] = useState<string | null>(null);

  const paperRef = useRef<HTMLDivElement>(null);

  const handleAddTopic = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && topicInput.trim()) {
      e.preventDefault();
      if (!topics.includes(topicInput.trim())) {
        setTopics([...topics, topicInput.trim()]);
      }
      setTopicInput("");
    }
  };

  const removeTopic = (index: number) => {
    setTopics(topics.filter((_, i) => i !== index));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!courseCode || topics.length === 0) {
      setError("Please provide course code and at least one topic.");
      return;
    }

    setLoading(true);
    setError(null);
    setPaper(null);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/generate-paper`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_code: courseCode,
          total_marks: totalMarks,
          difficulty,
          topics,
        }),
      });

      if (!res.ok) throw new Error(`Generation failed: ${res.statusText}`);

      const data = await res.json();
      setPaper(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleCopy = () => {
    if (!paper) return;
    
    let text = `QUESTION PAPER: ${paper.course_code}\n`;
    text += `Total Marks: ${paper.total_marks} | Difficulty: ${paper.difficulty}\n\n`;
    
    paper.sections.forEach(section => {
      text += `${section.title}\n`;
      section.questions.forEach(q => {
        text += `${q.number}. ${q.text} (${q.marks} marks)\n`;
        if (q.options) {
          q.options.forEach((opt, i) => {
            text += `   ${String.fromCharCode(97 + i)}) ${opt}\n`;
          });
        }
      });
      text += "\n";
    });

    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between print:hidden">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Question Paper Generator</h1>
            <p className="text-slate-500">Create AI-generated assessments from course materials</p>
          </div>
          <div className="flex gap-4">
            <Link 
              href="/faculty"
              className="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form */}
          <div className="lg:col-span-1 space-y-6 print:hidden">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Course Code</label>
                  <input
                    type="text"
                    value={courseCode}
                    onChange={(e) => setCourseCode(e.target.value.toUpperCase())}
                    className="w-full px-4 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-mono"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Total Marks</label>
                  <input
                    type="number"
                    value={totalMarks}
                    onChange={(e) => setTotalMarks(parseInt(e.target.value))}
                    className="w-full px-4 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-4 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all bg-white"
                  >
                    <option>Easy</option>
                    <option>Medium</option>
                    <option>Hard</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Topics</label>
                  <input
                    type="text"
                    value={topicInput}
                    onChange={(e) => setTopicInput(e.target.value)}
                    onKeyDown={handleAddTopic}
                    placeholder="Type and press Enter"
                    className="w-full px-4 py-2 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  />
                  <div className="flex flex-wrap gap-2 mt-3">
                    {topics.map((topic, i) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-medium border border-indigo-100">
                        {topic}
                        <button type="button" onClick={() => removeTopic(i)} className="hover:text-indigo-900">×</button>
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md shadow-indigo-100 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Generating...
                    </>
                  ) : (
                    "Generate Paper"
                  )}
                </button>
              </form>
            </div>
            
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                ⚠️ {error}
              </div>
            )}
          </div>

          {/* Paper Display */}
          <div className="lg:col-span-2">
            {paper ? (
              <div className="space-y-4">
                <div className="flex justify-end gap-3 print:hidden">
                  <button
                    onClick={handleCopy}
                    className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    Copy Text
                  </button>
                  <button
                    onClick={handlePrint}
                    className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
                  >
                    Print / Save PDF
                  </button>
                </div>

                <div 
                  ref={paperRef}
                  className="bg-white rounded-2xl p-8 md:p-12 shadow-sm border border-slate-200 print:shadow-none print:border-none print:p-0"
                >
                  <style jsx global>{`
                    @media print {
                      body { background: white !important; }
                      .print-hidden { display: none !important; }
                      @page { margin: 2cm; }
                    }
                  `}</style>
                  
                  {/* Paper Header */}
                  <div className="text-center border-b-2 border-slate-900 pb-6 mb-8">
                    <h2 className="text-xl font-bold uppercase tracking-tight">University Examination</h2>
                    <h3 className="text-lg font-semibold mt-1">Course: {paper.course_code}</h3>
                    <div className="flex justify-between mt-4 text-sm font-medium">
                      <span>Total Marks: {paper.total_marks}</span>
                      <span>Difficulty: {paper.difficulty}</span>
                      <span>Time: 3 Hours</span>
                    </div>
                  </div>

                  {/* Sections */}
                  <div className="space-y-8">
                    {paper.sections.map((section, si) => (
                      <div key={si}>
                        <h4 className="text-md font-bold uppercase border-b border-slate-200 pb-1 mb-4">
                          {section.title}
                        </h4>
                        <div className="space-y-6">
                          {section.questions.map((q, qi) => (
                            <div key={qi} className="relative pl-8">
                              <span className="absolute left-0 top-0 font-bold">{q.number}.</span>
                              <div className="flex justify-between gap-4">
                                <p className="text-slate-800 leading-relaxed">{q.text}</p>
                                <span className="font-mono text-sm whitespace-nowrap">({q.marks})</span>
                              </div>
                              {q.options && (
                                <div className="grid grid-cols-2 gap-2 mt-3 ml-2">
                                  {q.options.map((opt, oi) => (
                                    <div key={oi} className="text-sm text-slate-700">
                                      <span className="font-medium mr-2">{String.fromCharCode(97 + oi)})</span>
                                      {opt}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-12 pt-8 border-t border-slate-100 text-center text-xs text-slate-400 print:text-slate-300">
                    Generated by Adaptive Learning AI Tutor · {new Date().toLocaleDateString()}
                  </div>
                </div>
              </div>
            ) : !loading && (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-white rounded-2xl border-2 border-dashed border-slate-200 text-slate-400 p-8 text-center">
                <svg className="w-16 h-16 mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-lg font-medium">No Paper Generated Yet</p>
                <p className="text-sm max-w-xs mt-1">Configure the settings and click generate to create a new question paper.</p>
              </div>
            )}
            
            {loading && (
              <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-white rounded-2xl border border-slate-200 p-8 text-center">
                <div className="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mb-4" />
                <p className="text-lg font-medium text-slate-700">Generating Assessment...</p>
                <p className="text-sm text-slate-500 mt-1 italic">Analyzing course materials and formatting questions</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
