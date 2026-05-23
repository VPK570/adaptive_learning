"use client";

import { apiFetch } from "@/lib/api";
import { useState, useRef, useEffect, useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { source_title: string; page: number; content_type: string }[];
}

interface HistoryItem {
  role: "user" | "assistant";
  content: string;
}

interface Stats {
  total_chunks: number;
  text_chunks: number;
  image_chunks: number;
}

const EXAMPLE_QUESTIONS = [
  "What is a flip-flop and how does it work?",
  "Explain the difference between synchronous and asynchronous counters",
  "How do you design a modulo-6 counter?",
  "What is the difference between Mealy and Moore state machines?",
  "Explain the excitation table of a JK flip-flop",
  "What are the steps to design a synchronous counter?",
];

const STOP_WORDS = new Set(["a", "an", "the", "and", "or", "but", "for", "with", "about", "is", "are", "was", "were", "to", "in", "of", "on", "at", "by", "what", "how", "why", "who", "which", "where", "when", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their", "me", "him", "us", "them", "do", "does", "did", "have", "has", "had", "be", "been", "being", "can", "could", "should", "would", "will", "shall", "may", "might", "must"]);

function ChatContent() {
  const searchParams = useSearchParams();
  const initialCourse = searchParams.get("course") || "BAECE102";
  const [courseCode] = useState(initialCourse);
  const [sessionId, setSessionId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      const key = `session_id_${initialCourse}`;
      const stored = localStorage.getItem(key);
      if (stored) return stored;
      const newId = Math.random().toString(36).substring(7);
      localStorage.setItem(key, newId);
      return newId;
    }
    return null;
  });

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`session_id_${initialCourse}`, sessionId);
    }
  }, [sessionId, initialCourse]);
  
  const initialWelcome = useMemo(() => ({
    role: "assistant" as const,
    content:
      `👋 Welcome to the **${initialCourse}** AI Tutor!\n\n` +
      "I'm your Socratic learning assistant. Ask me anything about the course materials — and I'll guide you through the concepts with questions and hints.\n\n" +
      "💡 *Tip: Be specific for better answers. Try asking about a particular concept, circuit type, or design method.*",
  }), [initialCourse]);
  const [messages, setMessages] = useState<Message[]>([initialWelcome]);
  const [conversationHistory, setConversationHistory] = useState<HistoryItem[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await apiFetch(`/chat-history?course_code=${courseCode}&session_id=${sessionId}`);
      if (data && Array.isArray(data)) {
        const loadedMessages: Message[] = [initialWelcome, ...data.map((item: { role: "user" | "assistant", content: string }) => ({ role: item.role, content: item.content }))];
        setMessages(loadedMessages);
        setConversationHistory(data.map((item: { role: "user" | "assistant", content: string }) => ({ role: item.role, content: item.content })));
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  }, [courseCode, sessionId, initialWelcome]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, suggestions]);

  const sessionTopics = useMemo(() => {
    const words = messages
      .filter((m) => m.role === "user")
      .map((m) => m.content.toLowerCase().replace(/[^\w\s]/g, "").split(/\s+/))
      .flat();

    const counts: Record<string, number> = {};
    words.forEach((word) => {
      if (word.length > 2 && !STOP_WORDS.has(word)) {
        counts[word] = (counts[word] || 0) + 1;
      }
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map((entry) => entry[0]);
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent, question?: string) => {
    e?.preventDefault();
    const q = question || input.trim();
    if (!q || loading) return;

    setInput("");
    setError(null);
    setSuggestions([]);
    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setConversationHistory((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    // Save to localStorage for dashboard
    localStorage.setItem(`last_question_${courseCode}`, q);

    try {
       const data = await apiFetch(`/query`, {
        method: "POST",
        body: JSON.stringify({
          question: q,
          course_code: courseCode,
          session_id: sessionId,
          top_k: 5,
          language: "English",
          history: conversationHistory,
        }),
      });

      const assistantMsg: Message = {
        role: "assistant",
        content: data.response,
        sources: data.cited_sources,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setConversationHistory((prev) => [...prev, { role: "assistant", content: data.response }]);
      
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ Sorry, I ran into an error: ${msg}. Try again or check if the backend is running.` },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const clearChat = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/chat-history?course_code=${courseCode}&session_id=${sessionId}`, {
        method: "DELETE",
      });
    } catch {}
    setMessages([initialWelcome]);
    setConversationHistory([]);
    setSuggestions([]);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-white shadow-sm">
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm group-hover:bg-indigo-700 transition-colors">
              {courseCode.substring(0, 3)}
            </div>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-900">{courseCode} Tutor</span>
            </div>
            <p className="text-xs text-slate-500">VIT · Personalized Learning</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-4 text-xs text-slate-500">
          <button
            onClick={clearChat}
            className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 hover:text-slate-900 transition-colors font-medium"
          >
            Clear chat
          </button>
          {stats && (
            <span className="px-3 py-1 bg-slate-100 rounded-full hidden sm:inline-block">
              📚 {stats.text_chunks} text · 🖼 {stats.image_chunks} diagrams
            </span>
          )}
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
            {messages.map((msg, i) => {
              const isRefusal = msg.content.includes("I don't have enough information in the course materials");
              return (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-2xl rounded-2xl px-5 py-4 text-sm leading-relaxed relative group ${
                      msg.role === "user"
                        ? "bg-indigo-600 text-white rounded-br-md"
                        : `bg-white border text-slate-800 rounded-bl-md shadow-sm ${
                            isRefusal ? "border-amber-400 bg-amber-50/30" : "border-slate-200"
                          }`
                    }`}
                  >
                    {msg.role === "assistant" && (
                      <button
                        onClick={() => copyToClipboard(msg.content)}
                        className="absolute top-2 right-2 p-1.5 rounded-md bg-slate-50 text-slate-400 opacity-0 group-hover:opacity-100 hover:text-indigo-600 transition-all border border-slate-100 shadow-sm"
                        title="Copy to clipboard"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                      </button>
                    )}
                    
                    {isRefusal && (
                      <div className="absolute -top-2.5 right-10 px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-bold uppercase tracking-wider rounded border border-amber-200">
                        Out of scope
                      </div>
                    )}
                    {msg.content.split("\n").map((line, j) => {
                      if (line.startsWith("**") && line.endsWith("**")) {
                        return (
                          <p key={j} className={`font-semibold mt-2 ${msg.role === "user" ? "text-indigo-100" : "text-slate-900"}`}>
                            {line.slice(2, -2)}
                          </p>
                        );
                      }
                      if (line.startsWith("- ")) {
                        return (
                          <li key={j} className={`ml-4 ${msg.role === "user" ? "text-indigo-100" : "text-slate-700"}`}>
                            {line.slice(2)}
                          </li>
                        );
                      }
                      if (line.match(/\[Source:.*?\]/)) {
                        const parts = line.split(/(\s*\[Source:[^\]]+\])/);
                        return (
                          <p key={j} className={msg.role === "user" ? "text-indigo-100" : "text-slate-700"}>
                            {parts.map((p, k) =>
                              p.match(/\[Source:.*?\]/) ? (
                                <span key={k} className={`inline-block px-1.5 py-0.5 mx-0.5 rounded text-xs font-mono ${
                                  msg.role === "user" ? "bg-indigo-500 text-indigo-200" : "bg-slate-100 text-slate-500"
                                }`}>
                                  {p}
                                </span>
                              ) : (
                                <span key={k}>{p}</span>
                              )
                            )}
                          </p>
                        );
                      }
                      return line ? (
                        <p key={j} className={msg.role === "user" ? "text-indigo-100" : "text-slate-700"}>
                          {line}
                        </p>
                      ) : null;
                    })}

                    {msg.sources && msg.sources.length > 0 && (
                      <div className={`mt-3 pt-3 border-t text-xs ${msg.role === "user" ? "border-indigo-400 text-indigo-200" : "border-slate-100 text-slate-500"}`}>
                        <span className="font-medium">Sources cited:</span>
                        <ul className="mt-1 space-y-0.5">
                          {msg.sources.map((s, k) => (
                            <li key={k} className="opacity-80">
                              • {s.source_title} · Slide {s.page}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-5 py-4 shadow-sm">
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                    Thinking...
                  </div>
                </div>
              </div>
            )}

            {!loading && suggestions.length > 0 && (
              <div className="flex flex-col items-start gap-2 ml-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Suggested follow-ups:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(undefined, s)}
                      className="text-xs px-3 py-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all shadow-sm text-left max-w-xs"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="flex justify-center">
                <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700 max-w-xl">
                  ⚠️ {error}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-slate-200 bg-white px-6 py-4">
            <form onSubmit={handleSubmit} className="flex gap-3 max-w-3xl mx-auto">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Ask a question about ${courseCode}...`}
                rows={1}
                className="flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                style={{ minHeight: "48px", maxHeight: "200px" }}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="h-12 px-5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </form>

            {/* Example questions */}
            {messages.length === 1 && (
              <div className="mt-4 max-w-3xl mx-auto">
                <p className="text-xs text-slate-400 mb-2 font-medium uppercase tracking-wider">Try these:</p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSubmit(undefined, q)}
                      className="text-xs px-3 py-1.5 rounded-full bg-slate-100 hover:bg-indigo-100 hover:text-indigo-700 text-slate-600 transition-colors border border-slate-200"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <p className="text-center text-[10px] text-slate-400 mt-3 uppercase tracking-widest font-medium">
              Grounded in Course Materials • Cited Inline
            </p>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="w-64 border-l border-slate-200 bg-white p-4 overflow-y-auto hidden lg:block flex-shrink-0">
          <div className="mb-6">
            <Link 
              href="/progress"
              className="flex items-center justify-center gap-2 w-full py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm"
            >
              📊 View My Progress
            </Link>
          </div>

          {sessionTopics.length > 0 && (
            <div className="mt-8">
              <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Session Topics</h2>
              <div className="flex flex-wrap gap-2">
                {sessionTopics.map((topic, i) => (
                  <span key={i} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-md text-[10px] font-bold uppercase tracking-tight border border-indigo-100">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {stats && (
            <div className="mt-8 p-3 bg-slate-50 rounded-xl border border-slate-100">
              <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Vector Store</h3>
              <div className="space-y-1 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Text chunks</span>
                  <span className="font-mono font-medium">{stats.text_chunks}</span>
                </div>
                <div className="flex justify-between">
                  <span>Diagram chunks</span>
                  <span className="font-mono font-medium">{stats.image_chunks}</span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-1 mt-1">
                  <span>Total</span>
                  <span className="font-mono font-bold text-indigo-600">{stats.total_chunks}</span>
                </div>
              </div>
            </div>
          )}

          <div className="mt-8 p-3 bg-indigo-50 rounded-xl border border-indigo-100">
            <p className="text-xs text-indigo-700 font-bold mb-1 uppercase tracking-wider">Socratic Mode</p>
            <p className="text-xs text-indigo-600 leading-relaxed">
              I ask questions before giving answers. This helps you think deeply and retain concepts better.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}


export default function ChatPage() {
  return (
    <Suspense fallback={<div>Loading chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}

