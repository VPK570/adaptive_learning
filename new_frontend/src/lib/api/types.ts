// Auth
export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  name?: string;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  role: string;
}

// User
export interface User {
  id: number;
  email: string;
  role: string;
  name: string;
  created_at: string;
}

export interface UpdateUserRequest {
  name?: string;
}

// Course
export interface Course {
  course_code: string;
  course_name: string;
  description: string;
  icon: string;
  doc_count?: number;
  chunk_count?: number;
  created_at?: string;
  documents?: { name: string; file_url?: string; file_size?: number; doc_type?: string }[];
  student_count?: number;
  total_queries?: number;
}

export interface CourseCreate {
  course_code: string;
  course_name: string;
  description: string;
  icon?: string;
}

export interface CourseUpdate {
  course_name?: string;
  description?: string;
  icon?: string;
}

export interface CourseStats {
  course_code?: string;
  total_chunks: number;
  text_chunks?: number;
  image_chunks?: number;
  topics?: { topic: string; chunks: number }[];
  documents: { name: string }[];
  curriculum_docs?: { name: string }[];
}

// Quiz
export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  user_answer_index?: number;
  is_correct?: boolean;
  bloom_level?: number;
}

export interface QuizRequest {
  course_code: string;
  topic: string;
  count?: number;
  bloom_levels?: number[];
}

export interface SaveQuizRequest {
  course_code: string;
  topic: string;
  questions: QuizQuestion[];
  score: number;
  total: number;
  bloom_levels?: number[];
}

export interface SavedQuiz {
  id: string;
  course_code: string;
  topic: string;
  score: number;
  total: number;
  questions?: QuizQuestion[];
  bloom_levels?: number[];
  created_at: string;
}

// Flashcard
export interface Flashcard {
  question: string;
  answer: string;
  bloom_level?: number;
}

export interface FlashcardRequest {
  course_code: string;
  topic: string;
  count?: number;
  bloom_levels?: number[];
}

export interface SaveFlashcardRequest {
  course_code: string;
  topic: string;
  cards: Flashcard[];
}

export interface SavedFlashcardSet {
  id: string;
  course_code: string;
  topic: string;
  cards?: Flashcard[];
  times_studied?: number;
  best_recall?: number | null;
  last_recall?: number | null;
  created_at: string;
}

export interface RecordFlashcardRequest {
  known_count: number;
  total: number;
}

export interface RecordFlashcardResponse {
  id: string;
  times_studied: number;
  best_recall: number;
  last_recall: number;
  status: string;
}

export interface ChatFeedbackRequest {
  question: string;
  course_code: string;
  helpful: boolean;
}

// Chat
export interface QueryRequest {
  question: string;
  course_code: string;
  session_id?: string;
  top_k?: number;
  language?: string;
  mastery?: number | null;
  bloom_level?: number | null;
  image_ids?: string[];
  source_titles?: string[];
  topics?: string[];
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text?: string;
  content?: string;
  images?: string[];
  paragraphs?: string[];
  bullets?: { label: string; text: string }[];
  sources?: { file?: string; page?: number; source_title?: string; file_url?: string }[];
  verified?: boolean;
  verificationReason?: string;
}

// Structured Topics (from course_topic)
export interface StructuredTopic {
  topic_name: string;
  subtopics: string[];
  prerequisites: string[];
  bloom_level: string;
  learning_objectives: string[];
  order_index: number;
}

export interface TopicCoverageItem {
  topic_name: string;
  status: 'covered' | 'missing';
  chunk_count: number;
  subtopics: string[];
  bloom_level: string;
}

// Student stats (WS1)
export interface StudentCourseStat {
  course_code: string;
  overall_mastery: number;
  quizzes_taken: number;
}

export interface StudentStats {
  courses: StudentCourseStat[];
  total_quizzes: number;
  current_streak: number;
  active_days: number;
}

export interface StudentCourseMap {
  course_code: string;
  overall_mastery: number;
  next: { topic_id: string; priority: number }[];
  topics: {
    topic_id: string;
    topic_name: string;
    mastery_score: number;
    bloom_level: string;
    prerequisites: string[];
    status: 'mastered' | 'in_progress' | 'not_started';
    attempts: number;
  }[];
}

// Analytics
export interface Analytics {
  total_queries?: number;
  top_questions?: { question: string; count: number }[];
  questions_per_day?: Record<string, number>;
  weak_topics?: string[];
  suggested_revision?: string[];
  topic_coverage?: TopicCoverageItem[];
  bloom_mastery?: Record<number, number>;
  recent_questions?: { id: string; course_code: string; question: string; timestamp: string | null; out_of_scope: boolean }[];
}

// Paper
export interface PaperRequest {
  course_code: string;
  total_marks?: number;
  difficulty?: string;
  topics?: string[];
  top_k?: number;
  bloom_levels?: number[];
}

export interface GeneratedPaper {
  title: string;
  subtitle: string;
  durationMins: number;
  totalMarks: number;
  sections: PaperSection[];
}

export interface PaperSection {
  label: string;
  instructions: string;
  questions: PaperQuestion[];
}

export interface PaperQuestion {
  number: number;
  text: string;
  marks: number;
  bloom: string[];
}
