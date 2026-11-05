# Student Performance Portal

A comprehensive, AI-powered academic assessment and performance portal with role-based access control (Super Admin, Staff, Student), batch management, proctored examinations, automated Google Gemini AI test generation & code evaluation, mock interview scheduling with Google Meet / Zoom email invites, and interactive visual analytics.

---

## 📚 Complete Project Documentation

Detailed architecture specifications, database schemas, proctoring protocols, and implementation plans have been generated inside the [`docs/`](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/) directory:

1. [**System Requirements Specification (SRS)**](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/SYSTEM_REQUIREMENTS_SPECIFICATION.md)
   - Detailed user roles & permission matrix (Super Admin, Staff, Student)
   - Strict batch uniqueness and student enrollment rules (no student self-registration)
   - 3-tier test system per subject (MCQ, Coding Test, Mock Interview)
   - Browser anti-cheating & proctoring specifications (1-warning tab switch, clipboard lock, screenshot blocking, timer auto-submit, absenteeism)

2. [**Database Schema & Data Models**](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/DATABASE_AND_DATA_MODELS.md)
   - Entity-Relationship Diagram (ERD)
   - Django Model specifications: `UserProfile`, `StaffProfile`, `Batch`, `BatchStaffAssignment`, `Student`, `Subject`, `Test`, `MCQQuestion`, `CodingQuestion`, `TestAttempt`, `ProctoringIncident`, `MockInterview`

3. [**Proctoring & AI Pipeline Architecture**](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/PROCTORING_AND_AI_PIPELINE.md)
   - JavaScript client proctoring state machine & event listeners
   - Google Gemini API integration for PDF/DOCX syllabus text extraction
   - Structured JSON prompt engineering for MCQ and Coding question generation
   - In-browser Coding Notepad & Gemini AI code evaluation pipeline
   - Mock Interview scheduling & HTML email dispatcher (Google Meet / Zoom)

4. [**Analytics, Dashboards & Reporting**](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/ANALYTICS_AND_REPORTS.md)
   - Visual charts (Subject Radar, Assessment Comparison Bar, Timeline Growth Line, Batch Percentile)
   - Batch leaderboard & dynamic ranking algorithm
   - Single-click downloadable PDF student report cards

5. [**Implementation Roadmap & Verification Plan**](file:///c:/Users/Admin/Desktop/StudentPerformancePortal/docs/IMPLEMENTATION_ROADMAP.md)
   - Phased delivery plan (Phases 1 through 6)
   - Verification checklists and test criteria for each phase

---

## 🚀 Key Architectural Highlights

- **AI Engine**: Google Gemini API (`gemini-1.5-flash` / `gemini-1.5-pro`) for document parsing, test generation, and intelligent code review.
- **Coding Sandbox**: Distraction-free in-browser Notepad editor evaluated directly by Gemini AI for logic, edge cases, code quality, and efficiency.
- **Strict Proctoring**: 1-warning policy on tab-switching/window blur; instant auto-submit on 2nd violation; complete block on text copy, cut, paste, and screenshot shortcuts.
- **Mock Interviews**: Staff-scheduled slots with Google Meet / Zoom meeting links automatically emailed to students, followed by multi-criteria staff evaluation.
- **Interactive Visuals**: Rich Chart.js / ApexCharts dashboards displaying student progress, subject mastery, and batch standings.

