"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

interface Flashcard {
  question: string;
  answer: string;
}

interface SavedFlashcardSet {
  id: string;
  course_code: string;
  topic: string;
  cards: Flashcard[];
  created_at: string;
}

function FlashcardsContent() {
  const searchParams = useSearchParams();
  const initialCourse = searchParams.get("course") || "";

  const [courseCode, setCourseCode] = useState(initialCourse);
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(5);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedSets, setSavedSets] = useState<SavedFlashcardSet[]>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  const fetchSavedSets = async (code: string) => {
    if (!code) return;
    try {
      const res = await fetch(`${API_URL}/flashcards/saved?course=${code}`);
      if (res.ok) setSavedSets(await res.json());
    } catch {}
  };

  useEffect(() => {
    fetchSavedSets(courseCode);
  }, [courseCode]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setFlashcards([]);
    setCurrentIndex(0);
    setIsFlipped(false);

    try {
      const res = await fetch(`${API_URL}/flashcards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_code: courseCode, topic, count }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to generate flashcards");
      }

      const data = await res.json();
      setFlashcards(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const saveSet = async () => {
    try {
      const res = await fetch(`${API_URL}/flashcards/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_code: courseCode, topic, cards: flashcards }),
      });
      if (res.ok) {
        alert("Set saved!");
        fetchSavedSets(courseCode);
      }
    } catch (err) {
      alert("Failed to save");
    }
  };

  const deleteSet = async (id: string) => {
    if (!confirm("Are you sure?")) return;
    try {
      await fetch(`${API_URL}/flashcards/saved/${id}`, { method: "DELETE" });
      fetchSavedSets(courseCode);
    } catch {}
  };

  const loadSavedSet = (set: SavedFlashcardSet) => {
    setFlashcards(set.cards);
    setTopic(set.topic);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  const nextCard = () => {
    if (currentIndex < flashcards.length - 1) {
      setIsFlipped(false);
      setTimeout(() => setCurrentIndex(currentIndex + 1), 150);
    }
  };

  const prevCard = () => {
    if (currentIndex > 0) {
      setIsFlipped(false);
      setTimeout(() => setCurrentIndex(currentIndex - 1), 150);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Flashcards</h1>
            <p className="text-slate-500">Master concepts through active recall</p>
          </div>
          <Link href="/" className="text-indigo-600 font-medium hover:underline">
            Back to Course
          </Link>
        </div>

        {/* Setup Form */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mb-8">
          <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="md:col-span-1">
              <label className="block text-sm font-medium text-slate-700 mb-1">Course Code</label>
              <input
                type="text"
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value.toUpperCase())}
                placeholder="e.g. CS101"
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1">Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Neural Networks"
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                required
              />
            </div>
            <div className="md:col-span-1">
              <label className="block text-sm font-medium text-slate-700 mb-1">Count</label>
              <select
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
              >
                <option value={5}>5 Cards</option>
                <option value={10}>10 Cards</option>
                <option value={15}>15 Cards</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="md:col-span-4 w-full py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {loading ? "Generating Flashcards..." : "Generate Flashcards"}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-8">
            {error}
          </div>
        )}

        {/* Flashcard Display */}
        {flashcards.length > 0 && (
          <div className="flex flex-col items-center">
            <div className="flex justify-between items-center w-full max-w-lg mb-4">
              <div className="text-sm font-bold text-slate-500 uppercase tracking-widest">
                Card {currentIndex + 1} of {flashcards.length}
              </div>
              <button 
                onClick={saveSet}
                className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 font-medium"
              >
                Save this set
              </button>
            </div>

            <div 
              className="relative w-full max-w-lg h-80 cursor-pointer perspective-1000"
              onClick={() => setIsFlipped(!isFlipped)}
            >
              <div 
                className={`relative w-full h-full transition-transform duration-500 transform-style-3d ${isFlipped ? 'rotate-y-180' : ''}`}
              >
                {/* Front */}
                <div className="absolute w-full h-full backface-hidden bg-white border-2 border-slate-200 rounded-3xl shadow-lg flex items-center justify-center p-8 text-center">
                  <div>
                    <span className="text-xs font-bold text-indigo-500 uppercase block mb-2">Question</span>
                    <p className="text-xl font-medium text-slate-800">{flashcards[currentIndex].question}</p>
                    <p className="mt-8 text-sm text-slate-400">Click to reveal answer</p>
                  </div>
                </div>

                {/* Back */}
                <div className="absolute w-full h-full backface-hidden bg-indigo-600 rounded-3xl shadow-lg flex items-center justify-center p-8 text-center rotate-y-180">
                  <div>
                    <span className="text-xs font-bold text-indigo-200 uppercase block mb-2">Answer</span>
                    <p className="text-xl font-medium text-white">{flashcards[currentIndex].answer}</p>
                    <p className="mt-8 text-sm text-indigo-300">Click to see question</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <button
                onClick={prevCard}
                disabled={currentIndex === 0}
                className="px-6 py-2 bg-white border border-slate-200 rounded-xl font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-30 transition-all"
              >
                Previous
              </button>
              <button
                onClick={nextCard}
                disabled={currentIndex === flashcards.length - 1}
                className="px-6 py-2 bg-indigo-600 rounded-xl font-bold text-white hover:bg-indigo-700 disabled:opacity-30 transition-all"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Saved Sets Section */}
        {savedSets.length > 0 && (
          <div className="mt-16">
            <h2 className="text-xl font-bold text-slate-900 mb-6">Saved Sets</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {savedSets.map((set) => (
                <div key={set.id} className="bg-white p-5 rounded-xl border border-slate-200 flex justify-between items-center shadow-sm">
                  <div>
                    <h3 className="font-semibold text-slate-800">{set.topic}</h3>
                    <p className="text-xs text-slate-500">{new Date(set.created_at).toLocaleDateString()} • {set.cards.length} cards</p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => loadSavedSet(set)}
                      className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-200 font-medium"
                    >
                      Load
                    </button>
                    <button 
                      onClick={() => deleteSet(set.id)}
                      className="text-xs bg-red-50 text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-100 font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && flashcards.length === 0 && !error && (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-200">
            <div className="text-6xl mb-4">🗂️</div>
            <h3 className="text-xl font-bold text-slate-800">No Flashcards Yet</h3>
            <p className="text-slate-500">Enter a course and topic above to generate study cards.</p>
          </div>
        )}
      </div>

      <style jsx global>{`
        .perspective-1000 {
          perspective: 1000px;
        }
        .transform-style-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
      `}</style>
    </div>
  );
}

export default function FlashcardsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <FlashcardsContent />
    </Suspense>
  );
}
