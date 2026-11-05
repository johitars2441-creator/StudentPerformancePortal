# Student Performance Portal - System Requirements Specification (SRS)

## 1. Executive Summary
The **Student Performance Portal** is a web-based academic assessment and analytics platform designed for educational institutions and training academies. The system features a role-based access control (RBAC) hierarchy comprising three user categories: **Super Admin**, **Staff**, and **Students**.

The platform is designed around structured **Batches**, subject assessments, an **AI-driven testing module** powered by the **Google Gemini API**, a **proctored exam environment** with strict anti-cheating controls, **Mock Interview management with automated meeting invitations**, and an **interactive visual analytics engine** for tracking student growth and performance trends.

---

## 2. User Roles & Access Control Specification

### 2.1 Role Matrix Overview

| Module / Operation | Super Admin | Staff | Student |
| :--- | :---: | :---: | :---: |
| **Manage Staff Accounts** | Full Control (Create, Edit, Deactivate) | No Access | No Access |
| **Manage Batches** | Full Control (Create, Assign Staff) | View Assigned Only | View Enrolled Batch Only |
| **Enroll Students** | Can add to any batch | Can add to assigned batches only | **Cannot self-register** |
| **Upload Syllabus Documents (PDF/DOCX)** | Full Access | Assigned batches only | No Access |
| **Create AI Tests (MCQ & Coding)** | Full Access | Assigned batches only | No Access |
| **Define Duration, Marks & Schedule** | Full Access | Assigned batches only | No Access |
| **Schedule Mock Interviews & Email Invites** | Full Access | Assigned batches only | Receive Invite & View Info |
| **Grade Mock Interviews** | Full Access | Assigned batches only | View Marks & Feedback |
| **Attend Tests** | No Access | No Access | Attend in active window |
| **View Analytics & Visual Graphs** | System-wide | Assigned Batches & Students | Personal Performance & Ranks |
| **Download PDF Performance Cards** | Any Student / Batch | Assigned Students | Own Performance Card |

---

### 2.2 Role Definitions

#### 1. Super Admin
- Top-level administrator with full system privileges.
- Creates, manages, and deactivates Staff accounts.
- Creates unique **Batches** (e.g., `BATCH-2026-FS01`). Each batch must possess a strictly unique code across the portal.
- Assigns batches to Staff members (one staff member can manage multiple batches; one batch can have multiple assigned staff).
- Retains global oversight across all batches, staff members, tests, and student analytics.

#### 2. Staff
- Scoped strictly to batches assigned by the Super Admin.
- **Student Onboarding**: Authorized to add students into their assigned batches. Students **cannot** self-register or assign themselves to any batch.
- **Assessment Management**:
  - Manages the three assessment types per subject: **MCQ Test**, **Coding Test**, and **Mock Interview**.
  - Uploads syllabus/source documents (**PDF** or **DOCX**) to trigger automated test creation using the Google Gemini API.
  - Configures test parameters: Total Marks, Duration (minutes), and Active Testing Time Window (Start and End Datetime).
  - Creates Mock Interview schedules, specifies meeting links (Google Meet or Zoom), and triggers automated calendar/invite emails to students.
  - Enters marks and comprehensive qualitative feedback post-interview.
- **Analytics & Reporting**:
  - Views individual student progress dashboards, comparative batch analytics, and student attendance/absenteeism logs.

#### 3. Student
- Account is created and enrolled into a batch by Staff or Super Admin. Self-registration is strictly prohibited.
- Receives automated login credentials and notifications upon enrollment.
- Accesses an interactive **Performance Dashboard** featuring graphs and charts tracking their scores, skill growth, and rank.
- Attends scheduled tests within the defined active window in a **strictly proctored, anti-cheat environment**.
- Writes code in a dedicated **Coding Notepad** during coding assessments.
- Receives automated, AI-evaluated results, ranks, and downloadable PDF performance scorecards.
- Receives Mock Interview meeting invitations (Google Meet/Zoom) via email and views staff feedback in their portal.

---

## 3. Academic Structure: Batches & Subjects

### 3.1 Batch Isolation & Uniqueness
- Each Batch must be uniquely identified by an alphanumeric code (e.g., `BATCH-PY-2026-A`).
- Duplication of batch identifiers is prohibited at the database constraint level.
- Every student belongs to exactly one active batch.
- Staff access is strictly partitioned: a staff member cannot view, modify, or grade students from batches they are not assigned to.

### 3.2 Subject & Assessment Model
Each batch is associated with specific subjects. For every subject in a batch, three standard assessment categories exist:
1. **MCQ Test**: AI-generated from uploaded documents; deterministically auto-graded with AI explanations.
2. **Coding Test**: AI-generated problem statements and scenarios; solved in a clean in-browser Notepad editor and evaluated by Gemini AI for logic, correctness, edge-case coverage, and code hygiene.
3. **Mock Interview**: Scheduled by staff with Google Meet / Zoom links sent via email; graded manually by staff with qualitative feedback.

---

## 4. Test Creation & AI Integration (Google Gemini API)

### 4.1 Document Ingestion
- Staff uploads reference study material, syllabus notes, or topic outlines in **PDF** or **Word (.docx)** format.
- System extracts plain text from the document using `pypdf` / `python-docx` and cleans whitespace and formatting.

### 4.2 AI Question Generation Engine
- The extracted text is injected into specialized prompts sent to the **Google Gemini API** (`gemini-1.5-flash` / `gemini-1.5-pro`):
  - **MCQ Generator Prompt**: Produces a structured JSON payload containing questions, 4 distinct options (A, B, C, D), the correct option key, an explanation, and assigned marks.
  - **Coding Problem Prompt**: Produces structured problem titles, detailed scenario descriptions, input/output formats, constraints, sample test cases, and hidden evaluation rubrics.
- **Staff Review & Approval**: Generated questions are presented in an editable preview interface. Staff can approve, edit, or regenerate specific questions before publishing the test.

---

## 5. Proctored Exam Environment & Anti-Cheating Protocol

To guarantee test integrity, student test sessions run under strict browser-level surveillance:

### 5.1 Fullscreen Mode & Screen Locking
- The student must enter full-screen mode to begin the test.
- Leaving full-screen triggers a warning modal and is logged as an integrity event.

### 5.2 1-Warning Tab-Switch Policy
- Monitored via the HTML5 Page Visibility API (`document.visibilityState`) and window focus events (`window.onblur`).
- **First Tab Switch / Window Blur**:
  - The exam window immediately freezes.
  - A modal appears: *"Warning 1/1: Tab switch or app switch detected! Any further switch will automatically terminate and submit your test."*
  - The student must acknowledge the warning to resume.
- **Second Tab Switch / Window Blur**:
  - The test session is **instantly auto-submitted**.
  - Test status is updated to `TERMINATED_VIOLATION`.
  - The student is locked out of further submissions.

### 5.3 Anti-Copying & Anti-Screenshot Restrictions
- **Clipboard Block**: `copy`, `cut`, and `paste` events are blocked via `event.preventDefault()`.
- **Context Menu Block**: Right-click context menus are completely disabled on the exam viewport.
- **Text Selection Block**: CSS rule `user-select: none` prevents highlighting or dragging text.
- **Keyboard Shortcut Interception**: Key combinations such as `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `PrintScreen`, `F12`, and `Ctrl+Shift+I` (DevTools) are captured and cancelled.

### 5.4 Countdown Timer & Auto-Submission
- A synchronized countdown timer displays remaining time.
- When the timer reaches `00:00`, current answers in the MCQ form or Coding Notepad are bundled and automatically submitted to the backend.

### 5.5 Absenteeism Handling
- Each test defines a start and end datetime window.
- When the window expires, an automated task scans for students in the batch who have not initiated an attempt and marks them as **Absent** (Status: `ABSENT`, Marks: `0`).

---

## 6. Coding Test: In-Browser Notepad & AI Evaluation

### 6.1 Coding Notepad Interface
- Split-screen layout:
  - **Left Panel**: Problem statement, constraints, input/output requirements, and sample test cases.
  - **Right Panel**: Lightweight, distraction-free code editor/notepad supporting syntax highlighting, line numbers, and tab indentation.
- Language selector (Python, Java, C++, JavaScript).

### 6.2 AI Code Evaluation Engine (Google Gemini API)
- Upon submission, the student's raw code is sent to the Gemini API along with the problem specifications and scoring rubric.
- **Evaluation Criteria**:
  1. **Logical Correctness**: Does the code accurately solve the problem described?
  2. **Edge-Case Resilience**: Does it accommodate boundary conditions, empty inputs, or large numbers?
  3. **Code Quality & Readability**: Appropriate variable naming, modular structure, and formatting.
  4. **Algorithmic Efficiency**: Time and space complexity suitability.
- **Output**:
  - Score awarded (e.g., 22 / 25).
  - Detailed line-by-line feedback and constructive recommendations for improvement.

---

## 7. Mock Interview Management & Email Workflow

### 7.1 Scheduling
- Staff selects Batch, Student, Subject, Date, Time, and Duration.
- Staff inputs the meeting link (**Google Meet** or **Zoom**).

### 7.2 Automated Email Delivery
- System sends an automated HTML notification email via Django's email service containing:
  - Interview date, time, and timezone.
  - Subject and Interviewer Staff name.
  - Direct **"Join Google Meet / Zoom"** action button.
  - Recommended preparation guidelines.

### 7.3 Staff Grading & Feedback
- After the interview, staff enters:
  - Quantitative Marks (out of maximum marks).
  - Parameter Ratings (Technical Depth, Communication, Problem Solving).
  - Detailed qualitative commentary highlighting strengths and weaknesses.

---

## 8. Analytics, Visual Dashboards & PDF Transcripts

### 8.1 Student Dashboard Visualizations (Chart.js / ApexCharts)
- **Subject Mastery Radar Chart**: Visualizes proficiency balance across all enrolled subjects.
- **Assessment Type Comparison Bar Chart**: Compares performance across MCQ, Coding, and Mock Interviews.
- **Historical Growth Line Chart**: Tracks performance trajectory over time.
- **Peer Standing Indicator**: Displays student score against the batch average and top score.

### 8.2 Batch Leaderboards & Rankings
- Dynamic batch-level ranking updated automatically upon evaluation completion.
- Percentile calculation and achievement badges.

### 8.3 Downloadable PDF Report Card
- Single-click export producing a branded, printable PDF document containing:
  - Student identity, roll number, and batch name.
  - Detailed scorecard across all subjects and assessment types.
  - AI code evaluation commentary and Staff mock interview notes.
  - Overall batch rank, grade, and percentage.

