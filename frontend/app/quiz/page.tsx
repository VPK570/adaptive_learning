"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

interface SavedQuiz {
  id: string;
  course_code: string;
  topic: string;
  questions: (QuizQuestion & { user_answer_index?: number; is_correct?: boolean })[];
  score: number;
  created_at: string;
}

function QuizContent() {
  const searchParams = useSearchParams();
  const initialCourse = searchParams.get("course") || "";

  const [courseCode, setCourseCode] = useState(initialCourse);
  const [topic, setTopic] = useState("");
  const [quizData, setQuizData] = useState<QuizQuestion[]>([]);
  const [userAnswers, setUserAnswers] = useState<Record<number, number>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [isReviewMode, setIsReviewMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pastQuizzes, setPastQuizzes] = useState<SavedQuiz[]>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

  const fetchPastQuizzes = async (code: string) => {
    if (!code) return;
    try {
      const res = await fetch(`${API_URL}/quiz/saved?course=${code}`);
      if (res.ok) setPastQuizzes(await res.json());
    } catch {}
  };

  useEffect(() => {
    fetchPastQuizzes(courseCode);
  }, [courseCode]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setQuizData([]);
    setUserAnswers({});
    setCurrentIndex(0);
    setShowResult(false);
    setIsReviewMode(false);

    try {
      const res = await fetch(`${API_URL}/quiz`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_code: courseCode, topic, count: 5 }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to generate quiz");
      }

      const data = await res.json();
      setQuizData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionIndex: number, selectedOption: number) => {
    if (userAnswers[questionIndex] !== undefined) return;
    setUserAnswers(prev => ({ ...prev, [questionIndex]: selectedOption }));
  };

  const saveQuiz = async () => {
    const questionsToSave = quizData.map((q, i) => ({
        ...q,
        user_answer_index: userAnswers[i] ?? -1,
        is_correct: userAnswers[i] === q.correct_index
    }));
    const score = questionsToSave.filter(q => q.is_correct).length;
    try {
      const res = await fetch(`${API_URL}/quiz/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_code: courseCode, topic, questions: questionsToSave, score }),
      });
      if (res.ok) {
        alert("Quiz attempt saved!");
        fetchPastQuizzes(courseCode);
      }
    } catch (err) {
      alert("Failed to save");
    }
  };

  const deleteQuiz = async (id: string) => {
    if (!confirm("Are you sure?")) return;
    try {
      await fetch(`${API_URL}/quiz/saved/${id}`, { method: "DELETE" });
      fetchPastQuizzes(courseCode);
    } catch {}
  };

  const reviewQuiz = (quiz: SavedQuiz) => {
    // Cast to QuizQuestion[] for compatibility with QuizQuestion state
    setQuizData(quiz.questions as QuizQuestion[]);
    // Reconstruct answers map for review
    const answers: Record<number, number> = {};
    quiz.questions.forEach((q, i) => {
        if (q.user_answer_index !== undefined && q.user_answer_index !== -1) {
            answers[i] = q.user_answer_index;
        }
    });
    setUserAnswers(answers);
    setShowResult(true);
    setIsReviewMode(true);
  };

  const nextQuestion = () => {
    if (currentIndex < quizData.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setShowResult(true);
    }
  };

  const resetQuiz = () => {
    setQuizData([]);
    setUserAnswers({});
    setCurrentIndex(0);
    setShowResult(false);
    setIsReviewMode(false);
  };

  const score = quizData.reduce((acc, q, i) => (userAnswers[i] === q.correct_index ? acc + 1 : acc), 0);

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{isReviewMode ? "Quiz Review" : "Quiz"}</h1>
            {!isReviewMode && <p className="text-slate-500">Test your knowledge and get instant feedback</p>}
          </div>
          <Link href="/" className="text-indigo-600 font-medium hover:underline">
            Back to Course
          </Link>
        </div>

        {/* Setup Form */}
        {!quizData.length && !showResult && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm mb-8">
            <form onSubmit={handleGenerate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
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
                  placeholder="e.g. History of Web"
                  className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="md:col-span-3 w-full py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {loading ? "Generating Quiz..." : "Start Quiz"}
              </button>
            </form>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-8">
            {error}
          </div>
        )}

        {/* Quiz Progress */}
        {quizData.length > 0 && !showResult && (
          <div className="mb-8">
            <div className="flex justify-between items-end mb-2">
              <span className="text-sm font-bold text-slate-400 uppercase">Question {currentIndex + 1} of {quizData.length}</span>
              <span className="text-sm font-bold text-indigo-600">Current Score: {score}</span>
            </div>
            <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${((currentIndex + 1) / quizData.length) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Question Display */}
        {quizData.length > 0 && !showResult && (
          <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="text-xl font-bold text-slate-800 mb-6">{quizData[currentIndex].question}</h2>
            
            <div className="space-y-3">
              {quizData[currentIndex].options.map((option, idx) => {
                const isSelected = userAnswers[currentIndex] === idx;
                const isAnswered = userAnswers[currentIndex] !== undefined;

                return (
                  <button
                    key={idx}
                    disabled={isAnswered}
                    onClick={() => handleAnswer(currentIndex, idx)}
                    className={`w-full p-4 text-left rounded-xl border-2 transition-all font-medium ${
                      isSelected ? "border-indigo-600 bg-indigo-50 text-indigo-700" :
                      "border-slate-100 bg-slate-50 hover:border-slate-300 text-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`w-8 h-8 rounded-lg flex items-center justify-center border-2 ${
                        isSelected ? "bg-indigo-600 border-indigo-600 text-white" :
                        "bg-white border-slate-200 text-slate-400"
                      }`}>
                        {String.fromCharCode(65 + idx)}
                      </span>
                      {option}
                    </div>
                  </button>
                );
              })}
            </div>

            {userAnswers[currentIndex] !== undefined && (
              <div className="mt-8 animate-in fade-in slide-in-from-top-4 duration-300">
                <div className={`p-4 rounded-xl mb-6 ${userAnswers[currentIndex] === quizData[currentIndex].correct_index ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"}`}>
                  <p className="font-bold mb-1">{userAnswers[currentIndex] === quizData[currentIndex].correct_index ? "✓ Correct!" : "✗ Incorrect"}</p>
                  <p className="text-sm">{quizData[currentIndex].explanation}</p>
                </div>
                <button
                  onClick={nextQuestion}
                  className="w-full py-4 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-100"
                >
                  {currentIndex === quizData.length - 1 ? "Finish Quiz" : "Next Question"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Results Screen */}
        {showResult && (
          <div className="text-center py-12 bg-white rounded-3xl border border-slate-200 shadow-xl p-8">
            {isReviewMode ? (
                <>
                    <h2 className="text-3xl font-bold text-slate-900 mb-8">Review Quiz</h2>
                    <div className="text-left space-y-6">
                        {quizData.map((q, idx) => {
                            const userAnswer = userAnswers[idx];
                            const isCorrect = userAnswer === q.correct_index;
                            return (
                                <div key={idx} className="p-6 bg-slate-50 rounded-xl border border-slate-200">
                                    <p className="font-bold mb-4">{idx + 1}. {q.question}</p>
                                    <div className="space-y-2 mb-4">
                                        {q.options.map((opt, optIdx) => {
                                            const isCorrectOption = optIdx === q.correct_index;
                                            const isUserAnswer = optIdx === userAnswer;
                                            return (
                                                <div key={optIdx} className={`p-3 rounded-lg border ${
                                                    isCorrectOption ? "bg-green-100 border-green-500" :
                                                    isUserAnswer && !isCorrectOption ? "bg-red-100 border-red-500" :
                                                    "bg-white"
                                                }`}>
                                                    {opt} {isCorrectOption && "(Correct)"} {isUserAnswer && !isCorrectOption && "(Your answer)"}
                                                </div>
                                            )
                                        })}
                                    </div>
                                    <p className="text-sm text-slate-600 italic">{q.explanation}</p>
                                </div>
                            );
                        })}
                    </div>
                </>
            ) : (
                <>
                    <div className="text-6xl mb-4">🎉</div>
                    <h2 className="text-3xl font-bold text-slate-900 mb-2">Quiz Completed!</h2>
                    <p className="text-slate-500 mb-8">Great job on finishing the quiz.</p>
                    
                    <div className="inline-block p-8 rounded-full bg-indigo-50 border-4 border-indigo-100 mb-8">
                        <span className="text-5xl font-black text-indigo-600">{score}</span>
                        <span className="text-2xl font-bold text-indigo-300"> / {quizData.length}</span>
                    </div>

                    <div className="flex flex-col gap-3">
                        <button
                            onClick={saveQuiz}
                            className="w-full py-4 bg-indigo-50 text-indigo-700 font-bold rounded-xl hover:bg-indigo-100 transition-colors"
                        >
                            Save this Attempt
                        </button>
                    </div>
                </>
            )}
            
            <div className="flex flex-col gap-3 mt-6">
              <button
                onClick={resetQuiz}
                className="w-full py-4 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors"
              >
                {isReviewMode ? "Close Review" : "Try Again"}
              </button>
              <Link
                href="/"
                className="w-full py-4 bg-slate-100 text-slate-600 font-bold rounded-xl hover:bg-slate-200 transition-colors"
              >
                Back to Dashboard
              </Link>
            </div>
          </div>
        )}

        {/* Past Quizzes Section */}
        {pastQuizzes.length > 0 && !showResult && !quizData.length && (
          <div className="mt-16">
            <h2 className="text-xl font-bold text-slate-900 mb-6">Past Quizzes</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pastQuizzes.map((q) => (
                <div key={q.id} className="bg-white p-5 rounded-xl border border-slate-200 flex justify-between items-center shadow-sm">
                  <div>
                    <h3 className="font-semibold text-slate-800">{q.topic}</h3>
                    <p className="text-xs text-slate-500">{new Date(q.created_at).toLocaleDateString()} • Score: {q.score}/{q.questions.length}</p>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => reviewQuiz(q)}
                      className="text-xs bg-slate-100 text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-200 font-medium"
                    >
                      Review
                    </button>
                    <button 
                      onClick={() => deleteQuiz(q.id)}
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
        {!loading && !quizData.length && !showResult && !error && (
          <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-200">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-xl font-bold text-slate-800">Ready for a Quiz?</h3>
            <p className="text-slate-500">Enter a course and topic above to generate a custom quiz.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <QuizContent />
    </Suspense>
  );
}
