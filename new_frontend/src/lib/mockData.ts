// ── User objects ────────────────────────────────────────────────
export const mockStudentUser = { name: 'Alex Rivera', initials: 'AR', avatarUrl: null };
export const mockFacultyUser = { name: 'Dr. Sarah Chen', initials: 'SC', avatarUrl: null };
export const mockAdminUser   = { name: 'Dr. Alan Turing', initials: 'AT', avatarUrl: null };

// ── Student stats ──────────────────────────────────────────────
export const mockStudentStats = { mastery: 72, streak: 14, topicsCompleted: 38, quizzesTaken: 24 };

// ── Faculty stats ──────────────────────────────────────────────
export const mockFacultyStats = { totalStudents: 113, activeCourses: 4, avgEngagement: 78 };
export const mockFacultyActivity = [
  { id: 1, student: 'Marie Curie', course: 'CS 401', action: 'Submitted Quiz', time: '12 min ago' },
  { id: 2, student: 'Niels Bohr', course: 'CS 305', action: 'Asked AI', time: '34 min ago' },
  { id: 3, student: 'Rosalind Franklin', course: 'CS 401', action: 'Uploaded File', time: '1 hour ago' },
];

// ── Aliases so pages can use either name ───────────────────────
export const mockStudentCourses = [
  { id: "bio101", color: "secondary", title: "Advanced Biology", description: "Cellular structures, metabolic pathways, and genetic mechanisms explored through interactive models.", docCount: 24 },
  { id: "econ201", color: "primary", title: "Macroeconomics", description: "Global market dynamics, fiscal policies, and economic indicators analysis using AI datasets.", docCount: 18 },
  { id: "psych210", color: "tertiary", title: "Cognitive Psychology", description: "Study of mental processes including perception, thinking, memory, and problem solving.", docCount: 32 },
];

export const mockFacultyCourses = [
  { id: "cs401", code: "cs401", title: "CS 401: Artificial Intelligence", term: "Fall 2024", students: 48, status: "Active" },
  { id: "cs305", code: "cs305", title: "CS 305: Machine Learning Basics", term: "Fall 2024", students: 65, status: "Active" },
];

export const studentCourses = [
  { id: "bio101", color: "secondary", title: "Advanced Biology", description: "Cellular structures, metabolic pathways, and genetic mechanisms explored through interactive models.", docCount: 24 },
  { id: "econ201", color: "primary", title: "Macroeconomics", description: "Global market dynamics, fiscal policies, and economic indicators analysis using AI datasets.", docCount: 18 },
  { id: "psych210", color: "tertiary", title: "Cognitive Psychology", description: "Study of mental processes including perception, thinking, memory, and problem solving.", docCount: 32 },
];

export const studentActivity = [
  { id: 1, time: "2 hours ago", color: "primary", text: "Asked AI about", highlight: "Photosynthesis light-dependent reactions" },
  { id: 2, time: "Yesterday", color: "secondary", text: "Uploaded new document:", highlight: "Q3_Economic_Report.pdf" },
  { id: 3, time: "2 days ago", color: "outline", text: "Completed practice quiz for", highlight: "Cognitive Psychology", highlightMuted: true },
];

export const facultyCourses = [
  { code: "cs401", title: "CS 401: Artificial Intelligence", term: "Fall 2024", students: 48, status: "Active" },
  { code: "cs305", title: "CS 305: Machine Learning Basics", term: "Fall 2024", students: 65, status: "Active" },
];

export const recentUploads = [
  { name: "Week 4 Lecture Notes.pdf", course: "CS 401", status: "ready" },
  { name: "Neural Nets Intro.pptx", course: "CS 305", status: "processing" },
  { name: "Midterm_Draft_v2.docx", course: "CS 401", status: "ready" },
];

export const topTopics = [
  { topic: "Backpropagation Details", queries: 42 },
  { topic: "Gradient Descent Optimization", queries: 28 },
  { topic: "Activation Functions", queries: 15 },
];

export const uploadQueue = [
  { id: 1, name: "Lec04_Neural_Networks.pdf", status: "uploading", progress: 75 },
  { id: 2, name: "Syllabus_Fall2024.pdf", status: "ready", progress: 100 },
];

export const courseMaterials = [
  { id: "a", name: "Attention Is All You Need.pdf", pages: 15, chunks: 142, status: "ready" },
  { id: "b", name: "Lec03_Transformers_Deep_Dive.pdf", status: "processing" },
  { id: "c", name: "Assignment_1_Instructions.pdf", pages: 4, chunks: 28, status: "ready" },
  { id: "d", name: "Course_Policies_and_Ethics.pdf", pages: 8, chunks: 65, status: "ready" },
];

export const courseDetail = {
  code: "econ201",
  title: "Macroeconomics",
  professor: "Prof. E. Thompson",
  term: "Fall Semester 2024",
  mastery: 68,
  nextItem: "Fiscal Policy Quiz",
  materials: [
    { id: 1, name: "Syllabus_ECON201_Fall.pdf", meta: "4 Pages • 1.2 MB", active: false },
    { id: 2, name: "Ch4_Monetary_Policy_Notes.pdf", meta: "24 Pages • Active Context", active: true },
    { id: 3, name: "Problem_Set_3_Inflation.pdf", meta: "8 Pages • Due in 2 days", active: false },
  ],
};

export const chatMessages = [
  { id: 1, role: "user", text: "Can you explain how central banks use the reserve requirement to control the money supply? Reference chapter 4." },
  {
    id: 2,
    role: "assistant",
    paragraphs: [
      "Certainly. According to your notes on Monetary Policy (Chapter 4), central banks use the reserve requirement as one of their primary tools to manage the money supply.",
    ],
    boldTerm: "reserve requirement",
    bullets: [
      { label: "To increase money supply:", text: "The central bank lowers the reserve requirement. Banks can lend out a higher percentage of their deposits, increasing the money multiplier effect." },
      { label: "To decrease money supply:", text: "The central bank raises the reserve requirement. Banks must hold more money in reserve, restricting lending and slowing economic activity." },
    ],
    sources: [
      { file: "Ch4_Monetary_Policy_Notes.pdf", page: 12 },
      { file: "Ch4_Monetary_Policy_Notes.pdf", page: 15 },
    ],
  },
];

export const adminStats = [
  { label: "Total Users", value: "1,240", icon: "Users", accent: "primary", trend: "+12% this month" },
  { label: "Total Courses", value: "86", icon: "Library", accent: "tertiary", trend: "+3 this week" },
  { label: "Docs Processed", value: "3,400", icon: "FileText", accent: "secondary", trend: "+450 today" },
  { label: "AI Conversations", value: "15.2k", icon: "MessagesSquare", accent: "primary-container", trend: "+2k this week" },
];

export const adminUsers = [
  { id: 1, name: "Dr. Alan Turing", email: "alan.t@uniai.edu", role: "admin", status: "active" },
  { id: 2, name: "Ada Lovelace", email: "ada.l@uniai.edu", role: "professor", status: "active" },
  { id: 3, name: "John von Neumann", email: "john.v@student.edu", role: "student", status: "offline" },
  { id: 4, name: "Grace Hopper", email: "grace.h@uniai.edu", role: "professor", status: "active" },
  { id: 5, name: "Richard Feynman", email: "richard.f@student.edu", role: "student", status: "active" },
];

export const platformActivity = [
  { label: "Mon", value: 2100 }, { label: "Tue", value: 3400 }, { label: "Wed", value: 2800 },
  { label: "Thu", value: 4500 }, { label: "Fri", value: 3800 }, { label: "Sat", value: 5200 }, { label: "Sun", value: 4200 },
];

export const recentSignups = [
  { name: "Marie Curie", time: "2 mins ago", role: "professor", avatarUrl: null },
  { name: "Niels Bohr", time: "15 mins ago", role: "student", avatarUrl: null },
  { name: "Erwin Schrödinger", time: "1 hour ago", role: "student", initials: "ED" },
  { name: "Rosalind Franklin", time: "3 hours ago", role: "professor", avatarUrl: null },
];

export const progressStats = [
  { label: "Total Conversations", value: "142", icon: "MessageSquare", trend: "+12% from last month" },
  { label: "Topics Explored", value: "38", icon: "Shapes", trend: "+5 new this week" },
  { label: "Most Active Course", value: "Quantum Mechanics", icon: "BookOpen", caption: "45 interactions" },
];

export const topicsBreakdown = [
  { topic: "Machine Learning", percent: 32, intensity: 1.0 },
  { topic: "Data Structures", percent: 25, intensity: 0.8 },
  { topic: "Linear Algebra", percent: 18, intensity: 0.6 },
  { topic: "Ethics in AI", percent: 15, intensity: 0.4 },
];

export const recommendedRevision = [
  { title: "Eigenvectors and Eigenvalues", note: "Linear Algebra - Low comprehension score detected." },
  { title: "Backpropagation Algorithm", note: "Machine Learning - Frequent clarification requests." },
];

export const generateSections = [
  { id: "a", title: "Section A: Short Answer", questions: 10, marksPerQ: 2 },
  { id: "b", title: "Section B: Long Essay", questions: 4, marksPerQ: 20 },
];

export const generatedPaper = {
  title: "CS401: Advanced Data Structures",
  subtitle: "Mid-Semester Examination - Fall 2024",
  durationMins: 180,
  totalMarks: 100,
  sections: [
    {
      label: "Section A",
      instructions: "Attempt all questions. (10 x 2 = 20 Marks)",
      questions: [
        { number: 1, text: "Define a B-Tree. State the minimum and maximum number of keys a B-Tree node of order 'm' can hold.", marks: 2, bloom: ["Remember"] },
        { number: 2, text: "Explain the difference between a min-heap and a max-heap with a small diagrammatic example.", marks: 2, bloom: ["Understand"] },
      ],
    },
    {
      label: "Section B",
      instructions: "Attempt any four questions. (4 x 20 = 80 Marks)",
      questions: [
        { number: 11, text: "(a) Construct an AVL tree by inserting the following sequence of numbers: 10, 20, 30, 40, 50, 25. Show the tree after each insertion and specify the rotations performed.\n(b) Prove that the height of an AVL tree with 'n' nodes is O(log n).", marks: 20, bloom: ["Apply", "Analyze"] },
      ],
    },
  ],
};
