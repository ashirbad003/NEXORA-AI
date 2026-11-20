import os

modules = [
    ('BRAIN', 'Module A: Unified AI Brain', [
        ('Central AI Provider Abstraction Interface', 'Multi-provider switching (Gemini, Local, Mock) with unified interface'),
        ('Student Context Aggregator', 'Compiles unified context (skills, past scores, weak areas, resume points)'),
        ('Deterministic Offline Fallback Engine', 'Provides rule-based and template-based responses when external AI APIs are offline'),
        ('Token & Cost Telemetry Tracker', 'Tracks prompt tokens, completion tokens, and estimated cost per call'),
        ('AI Prompt Safety & Sanitization Filter', 'Sanitizes user input before passing to AI to prevent prompt injection and jailbreaks'),
        ('AI Recommendation Explainability Engine', 'Provides rationale metrics for every AI output'),
        ('Context Window Optimization', 'Compresses conversation history to fit within LLM token budgets'),
        ('Model Response Schema Validator', 'Enforces strict JSON schema validation on all structured LLM responses'),
        ('Personalized AI Persona Manager', 'Configures AI tone (Strict Interviewer, Friendly Mentor, Technical Architect)'),
        ('Multi-turn Conversation Persistence', 'Stores multi-turn AI interactions with session IDs and message ordering'),
        ('AI Latency & Timeout Guardian', 'Enforces strict 10s timeouts on AI queries to prevent hanging threads'),
        ('Skill Gap Vector Matcher', 'Calculates semantic gap between user mastered skills and role requirements'),
        ('Realtime AI Streaming Support', 'Streams AI response tokens via Server-Sent Events (SSE) or WebSockets'),
        ('AI Output Confidence Score Estimator', 'Calculates confidence score (0.0 to 1.0) on generated explanations'),
        ('Automated AI Feedback Logging', 'Enables students to thumbs-up/down AI responses for quality tracking'),
        ('Career Readiness Index Calculator', 'Computes holistic readiness score (0-100) from all modules'),
        ('AI Rate Limiter & Quota Gate', 'Restricts free-tier users to 50 AI queries per day to prevent abuse'),
        ('Multi-Language Explanation Translator', 'Translates core learning explanations into regional languages'),
        ('Weakness Remediation Plan Generator', 'Synthesizes low-scoring assessment topics into immediate 7-day study plans'),
        ('AI Knowledge Graph Concept Linker', 'Maps user questions to core computer science knowledge graph nodes')
    ]),
    ('COPILOT', 'Module B: AI Career Copilot', [
        ('Personalized Career Path Selector', 'Allows students to select and configure target career tracks (SDE, Data, DevOps, FullStack)'),
        ('Dynamic 90-Day Placement Roadmap', 'Generates weekly step-by-step preparation timeline'),
        ('Daily Sprints & Actionable Goals', 'Breaks weekly milestones into daily bite-sized tasks'),
        ('Target Company Preparation Matrix', 'Customizes study roadmaps specifically for target companies'),
        ('Skill Benchmark Against Industry Standards', 'Compares student skill level with tier-1 company requirements'),
        ('Internship Readiness Evaluator', 'Evaluates eligibility and readiness for summer internships'),
        ('Weekly Progress Digest Generator', 'Generates weekly summary report of hours spent, problems solved, and growth'),
        ('Study Habit & Velocity Tracker', 'Monitors consistency, study hours, and problem-solving velocity over time'),
        ('Smart Project Recommendation Engine', 'Recommends portfolio projects tailored to target roles and unfilled resume gaps'),
        ('Peer Rank & Cohort Comparison', 'Displays anonymized percentile ranking within college batch or department'),
        ('Career Milestone Badge System', 'Awards celebratory badges upon completing major roadmap milestones'),
        ('AI Mentor Direct Q&A Console', 'Context-aware chat assistant dedicated to career questions and placement doubts'),
        ('Resume-Driven Roadmap Adjustment', 'Re-evaluates roadmap dynamically whenever student uploads a revised resume'),
        ('Interview Timeline Countdown', 'Tracks countdowns to upcoming placement drives and campus interviews'),
        ('Burnout & Fatigue Warning Detector', 'Detects prolonged high error rates or sudden drop in velocity and suggests breaks'),
        ('Target Salary & Compensation Insights', 'Provides realistic industry compensation ranges for target roles and locations'),
        ('Certification Recommendation Finder', 'Suggests recognized industry certifications that boost placement chances'),
        ('Campus Placement Eligibility Checker', 'Checks student GPA, backlogs, and attendance against college placement rules'),
        ('Daily Tech Trivia & Micro-Quiz', 'Presents single daily multiple-choice question to build daily habits'),
        ('Study Group Matcher', 'Matches students aiming for the same company or track into study circles')
    ]),
    ('ASSESS', 'Module C: Assessment Intelligence', [
        ('Timed Assessment Engine Core', 'Runs synchronized timed online tests with countdown and automatic submission'),
        ('Auto-Save Answer State', 'Saves selected answers asynchronously every 5 seconds to prevent data loss'),
        ('Interrupted Attempt Recovery', 'Allows resuming interrupted attempts if remaining time is greater than zero'),
        ('Question Randomization & Shuffling', 'Shuffles question order and option choices uniquely per student'),
        ('Negative Marking Evaluator', 'Supports customizable negative marking (e.g., -0.25, -0.5) per wrong answer'),
        ('Question Flagging for Review', 'Enables students to mark questions for review and jump via palette'),
        ('Sectional Time Limits & Switching', 'Supports multi-section tests (Aptitude, Coding, Core CS) with sectional timers'),
        ('Comprehensive Diagnostic Scorecard', 'Generates detailed post-test performance analysis with percentile and accuracy'),
        ('Detailed Solution & Explanation Viewer', 'Provides step-by-step solutions and concept explanations after test submission'),
        ('Adaptive Difficulty Engine', 'Dynamically adjusts next question difficulty based on prior answers'),
        ('Company-Specific Test Templates', 'Pre-configured test templates mimicking TCS NQT, Infosys, Wipro, and Amazon formats'),
        ('Subject & Topic-Wise Practice Tests', 'Allows students to generate custom quizzes on specific topics (e.g., DBMS, OS)'),
        ('Anti-Cheating Window Blur Detection', 'Tracks tab switching and window blur events with warning dialogs'),
        ('Historical Assessment Trends', 'Tracks test score trends over weeks to measure progress'),
        ('Weak Area Tag Extractor', 'Extracts recurring low-scoring tags from assessments to feed Smart Revision'),
        ('Leaderboard for Public Assessments', 'Calculates global ranking for open assessments with tie-breaking rules'),
        ('Question Report & Feedback System', 'Allows test-takers to report ambiguous questions or wrong answer keys'),
        ('Admin Question Bank CRUD', 'Enables administrators to create, update, review, and archive test questions'),
        ('Bulk Question CSV/JSON Importer', 'Allows admins to import hundreds of curated questions via CSV or JSON'),
        ('Assessment Retake Policy Controller', 'Configures whether a test can be retaken and cooldown period'),
        ('Assessment Certificate Generator', 'Generates downloadable PDF certificate of completion for qualifying scores'),
        ('Mock Drive Assessment Mode', 'Simulates complete multi-round assessment rounds for placement drives')
    ]),
    ('CODING', 'Module D: Coding Arena', [
        ('Monaco-Based Online Code Editor', 'Rich browser editor with syntax highlighting, line numbers, and theme switching'),
        ('Multi-Language Runtime Support', 'Execution support for Python, Java, C, and C++ with specific compiler flags'),
        ('Problem Catalog Browser', 'Filterable list of coding problems by difficulty, topic, and company tag'),
        ('Company-Wise Problem Filtering', 'Dedicated collections of questions asked at Google, Microsoft, Amazon, etc.'),
        ('Public Test Case Execution', 'Runs code against sample visible test cases with diff output'),
        ('Hidden Test Case Evaluation', 'Executes code against extensive hidden test suites to verify edge cases'),
        ('Process-Isolated Execution Sandbox', 'Executes user code in dedicated isolated worker with zero network and low privileges'),
        ('Strict Execution Timeouts', 'Terminates runaway loops after 3-5 seconds with TLE error report'),
        ('Memory Limit Ceilings', 'Restricts execution memory to 128MB with MLE error report'),
        ('Sanitized Output & Error Formatter', 'Sanitizes standard output, standard error, and compiler traces'),
        ('Detailed Submission History', 'Logs past submissions with status (AC, WA, TLE, MLE, CE), runtime, and memory'),
        ('Coding Streak & Activity Tracker', 'Records daily problem-solving activity and updates student streak'),
        ('Live Coding Contest Engine', 'Hosts timed competitive coding contests with real-time leaderboard'),
        ('Editorial Solution & Discussion Tab', 'Presents vetted optimal solutions, complexity notes, and community comments'),
        ('Problem Custom Input Runner', 'Allows testing arbitrary custom test inputs before final submission'),
        ('Plagiarism & Similarity Detection Hook', 'Detects duplicate code submissions across users using token hashing'),
        ('Curated Problem Bank of 1000+ Problems', 'Seed database containing 1,000+ categorized algorithmic challenges'),
        ('100+ Company Question Mappings', 'Problem relations mapped to 100 verified tech recruiters'),
        ('Submission Runtime Distribution Graph', 'Histogram showing student runtime vs. all accepted submissions'),
        ('Submission Memory Distribution Graph', 'Histogram showing student memory footprint vs. cohort'),
        ('Multi-File Project Playground', 'Mini IDE for multi-file code exploration and testing'),
        ('Bookmark & Solved Later List', 'Allows saving challenging problems to student revision queue'),
        ('Daily LeetCode/GFG Style Problem of the Day', 'Features a designated challenge every 24 hours with bonus XP'),
        ('Admin Coding Problem Authoring Portal', 'CRUD interface for adding problems, test cases, and reference solutions')
    ]),
    ('CODEREV', 'Module E: AI Code Review', [
        ('Static Code Quality Analyzer', 'Inspects code formatting, naming conventions, and style violations'),
        ('Algorithmic Bug & Logic Error Spotter', 'Identifies off-by-one errors, infinite loops, and unhandled nulls'),
        ('Asymptotic Complexity Estimator', 'Computes Big-O Time and Space complexity from AST and structure'),
        ('Code Optimization Recommender', 'Suggests faster data structures and algorithmic improvements'),
        ('Code Explanation & Step-by-Step Breakdown', 'Generates plain-language line-by-line explanation of code logic'),
        ('Edge-Case Vulnerability Highlighter', 'Flags unhandled edge cases (empty arrays, max integers, negative inputs)'),
        ('Naming & Clean Code Auditor', 'Provides actionable suggestions for descriptive variable and function names'),
        ('Security & Unsafe Function Scanner', 'Detects dangerous functions (eval, system calls, unchecked buffer access)'),
        ('Language-Specific Idiom Guidance', 'Provides Pythonic/Modern C++ idioms and best practices'),
        ('Refactored Code Diff Viewer', 'Side-by-side git-style diff comparing original code with AI-improved code'),
        ('Learning-Oriented Socratic Hints', 'Offers progressive hints instead of giving away full solutions'),
        ('Memory Leak & Resource Close Checker', 'Flags unclosed files, database handles, and memory allocation leaks'),
        ('Cyclomatic Complexity Metric Card', 'Visual indicator of code branches and cyclomatic complexity score'),
        ('Review History & Progress Tracker', 'Maintains log of all code reviews and student adherence over time'),
        ('Interactive Code Chat Assistant', 'Allows asking follow-up questions directly on selected lines of code'),
        ('Export Code Review Report', 'Generates downloadable Markdown / PDF summary of code audit')
    ]),
    ('INTERVIEW', 'Module F: Interview Intelligence', [
        ('AI Mock Interview Studio Core', 'Interactive multi-round interview simulation environment'),
        ('Browser Speech-to-Text Recognition', 'Web Speech API integration for real-time student voice transcription'),
        ('Speech Synthesis Audio Output', 'Natural audio vocalization of interviewer questions and prompts'),
        ('Text-Based Interview Fallback Mode', 'Complete text-based chat interface for environments without microphone'),
        ('Technical Deep-Dive Interview Mode', 'Algorithmic, system design, and language trivia questioning'),
        ('HR & Behavioral Interview Mode', 'Culture fit, situational, and behavioral questioning session'),
        ('Company-Specific Interview Personas', 'Customized interview tracks matching Google, Amazon, TCS, etc.'),
        ('Dynamic Contextual Follow-up Questions', 'Interviewer poses intelligent follow-ups based on student answers'),
        ('STAR Methodology Scorer', 'Evaluates responses based on Situation, Task, Action, and Result structure'),
        ('Communication Tone & Clarity Analyzer', 'Evaluates vocabulary, clarity, filler word frequency, and tone'),
        ('Answer Relevance & Technical Accuracy Metric', 'Scores how well the response directly answers the posed question'),
        ('Mock Interview History & Playback', 'Stores complete transcript and audio playback of past interview rounds'),
        ('Mistake & Blunder Analysis Card', 'Highlights factual errors, weak answers, or missed technical points'),
        ('Actionable Improvement Plan Generator', 'Generates tailored drills to improve identified interview weaknesses'),
        ('Interview Readiness Scorecard', 'Holistic 0-100 score indicating readiness for live campus interviews'),
        ('Timer & Pacing Coach', 'Tracks answer duration and warns when responses are too brief or rambling'),
        ('Behavioral Question Bank with Sample STAR Answers', 'Catalog of 200+ behavioral questions with exemplary answers'),
        ('System Design Interview Whiteboard Mode', 'Interactive architecture diagramming canvas integrated with interview'),
        ('Resume-Based Interview Questions', 'Pulls projects and claims from uploaded resume to formulate probing questions'),
        ('Admin Mock Interview Prompt & Template Manager', 'Allows configuring interview tracks, questions, and grading rubrics')
    ]),
    ('LEARN', 'Module G: Smart Learning Hub', [
        ('Interactive Concept Explorer Core', 'Structured interactive textbook for Computer Science concepts'),
        ('DSA Learning Path Curriculum', 'Comprehensive roadmap covering Arrays, Trees, Graphs, DP, and more'),
        ('Core CS Modules (OS, DBMS, CN, OOPS)', 'Curated topic notes, architecture diagrams, and practice quizzes'),
        ('AI Concept Tutor (Socratic Mode)', 'Ask doubts on any concept and receive progressive guided explanations'),
        ('Interactive Code Snippet Sandbox', 'Run and modify code examples directly inside learning articles'),
        ('Topic Mastery Progress Bar', 'Visual indicator of completed topics and retention status'),
        ('Rich Markdown & LaTeX Math Support', 'Renders mathematical formulas, recurrence relations, and tables beautifully'),
        ('Concept Video & Visual Resource Curator', 'Links curated high-quality free video lectures and animations'),
        ('Concept Practice Problem Embedder', 'Directly links relevant Coding Arena and Assessment questions to each topic'),
        ('Downloadable Concept Cheat Sheets', 'One-page summary PDF cheat sheets for quick revision'),
        ('Multilingual Learning Language Selector', 'Read concept notes in English, Hindi, and regional languages'),
        ('Offline Article Cache (PWA)', 'Service Worker cache allowing reading downloaded notes without internet'),
        ('Topic Difficulty Rating & User Feedback', 'Students rate topic difficulty and report confusing sections'),
        ('Concept Prerequisite Graph', 'Visual map showing prerequisite topics required before starting a module'),
        ('Real-World System Architecture Case Studies', 'Deep dives into architectures of Netflix, Uber, YouTube, and WhatsApp'),
        ('Interactive Flash Quiz Checkpoints', 'Mini 2-minute checkpoints interspersed within reading material'),
        ('Reading Time & Word Count Indicators', 'Estimated reading time badges on each concept guide'),
        ('Dark/Light Optimized Reader View', 'Distraction-free reading view with custom font sizing and typography'),
        ('Student Bookmarking & Personal Notes Drawer', 'Highlight text and save personal study notes anchored to paragraphs'),
        ('Admin Article & Curriculum CMS', 'Rich admin interface for authoring, updating, and publishing learning modules'),
        ('Full-Text Search across Learning Hub', 'Instant fuzzy search across all notes, topics, and code examples'),
        ('Curriculum Versioning & Changelog', 'Tracks updates to curriculum notes with historical revision diffs')
    ]),
    ('REVISION', 'Module H: Smart Revision & Spaced Repetition', [
        ('SuperMemo SM-2 Algorithm Engine', 'Calculates optimal review intervals based on difficulty and recall rating'),
        ('Digital Flashcard Deck Creator', 'Interactive flashcards with front/back flip animations'),
        ('Weak-Topic Auto-Deck Generator', 'Automatically generates flashcard decks from failed test and coding questions'),
        ('Daily Revision Target Counter', 'Shows exact number of flashcards due for review today'),
        ('Card Recall Rating Controls (Again, Hard, Good, Easy)', 'Standard 4-tier spaced repetition response grading'),
        ('Deck Mastery & Retention Metrics', 'Visual charts showing percentage of mature vs. learning cards'),
        ('Pre-Built Curated Flashcard Decks', 'Ready-to-use decks for SQL Queries, Time Complexities, System Design, OS'),
        ('Custom User Flashcard Authoring', 'Allows students to create, edit, and categorize custom study cards'),
        ('Spaced Repetition Calendar Heatmap', 'Shows historical review streaks and projected upcoming review load'),
        ('Audio Flashcard Pronunciation Support', 'Reads terminology and definitions aloud via speech synthesis'),
        ('Mistake Notebook & Error Log', 'Dedicated repository of all incorrect test answers and failed submissions'),
        ('Revision Session Timer & Focus Mode', 'Full-screen distraction-free flashcard review session'),
        ('Export / Import Anki Compatible Decks', 'Export decks to .tsv / JSON and import external Anki cards'),
        ('Deck Sharing with Study Groups', 'Share curated revision decks with cohort peers or study circles'),
        ('Flashcard Tagging & Search System', 'Tag cards by subject, company, or priority with instant filtering'),
        ('Smart Revision Push Notification Reminder', 'Scheduled alert reminding students when high-priority cards are due'),
        ('Retention Decay Predictor', 'Estimates memory decay curves over 30 days without revision'),
        ('Admin Flashcard Bank Moderation', 'Admin interface for approving community-shared decks')
    ]),
    ('DSAVIZ', 'Module I: DSA Visualizer', [
        ('Graph Traversal: Breadth-First Search (BFS)', 'Step-by-step queue visualization with visited node highlighting'),
        ('Graph Traversal: Depth-First Search (DFS)', 'Step-by-step recursion stack visualization with backtracking'),
        ('Shortest Path: Dijkstra Algorithm', 'Priority queue and distance table step-by-step updates'),
        ('Shortest Path: Bellman-Ford Algorithm', 'Edge relaxation rounds and negative cycle detection display'),
        ('All-Pairs Shortest Path: Floyd-Warshall', 'Distance matrix transition visualization across all vertex pairs'),
        ('Directed Graph: Topological Sort', 'Kahn algorithm in-degree tracking and visual node ordering'),
        ('Graph Cycle Detection (Directed & Undirected)', 'Cycle discovery visualization using coloring / Union-Find'),
        ('Minimum Spanning Tree: Kruskal Algorithm', 'Disjoint Set Union (DSU) operations and edge sorting visualizer'),
        ('Minimum Spanning Tree: Prim Algorithm', 'Cut property and growing MST tree visualization'),
        ('DP: 0/1 Knapsack Problem', 'Dynamic 2D table computation with item selection backtrack path'),
        ('DP: Longest Common Subsequence (LCS)', 'Grid matrix animation with diagonal arrow transitions and backpointer trace'),
        ('DP: Longest Increasing Subsequence (LIS)', 'Array DP state updates and patience sorting visualization'),
        ('DP: Coin Change Problem', '1D/2D memoization array animation showing optimal coin combinations'),
        ('DP: Fibonacci Number (Memoization vs Tabulation)', 'Recursion tree comparison against linear iterative table fill'),
        ('DP: Matrix Chain Multiplication', 'Cost matrix calculation and optimal parenthesis bracket tree'),
        ('DP: Edit Distance (Levenshtein)', 'Interactive grid showing Insert, Delete, and Replace operations'),
        ('Interactive Graph Builder & Custom Input', 'Allows users to draw nodes and edges on a canvas and run any algorithm'),
        ('Execution Speed Slider & Play/Pause/Step Controls', 'Granular control over animation speed with step-by-step navigation')
    ]),
    ('RESUME', 'Module J: Resume Intelligence', [
        ('Resume PDF & DOCX Parser', 'Extracts text, contact details, education, skills, and work experience'),
        ('ATS Compatibility Scorer (0-100)', 'Analyzes parsing compatibility, formatting errors, and section headings'),
        ('Job Description Match & Gap Analyzer', 'Compares resume text against target job descriptions and flags missing keywords'),
        ('Hard & Soft Skill Extractor', 'Categorizes extracted skills into Languages, Frameworks, Tools, and Concepts'),
        ('Quantified Impact Bullet Point Auditor', 'Evaluates work experience bullets for strong action verbs and metrics (XYZ formula)'),
        ('AI Bullet Point Rewriter & Enhancer', 'Transforms weak resume bullet points into high-impact accomplishment statements'),
        ('LaTeX & PDF Exportable Resume Builder', 'Interactive form-based resume builder generating clean, ATS-compliant formats'),
        ('Modern Professional Resume Templates', 'Curated collection of Harvard, Tech, and Minimalist resume templates'),
        ('Resume Version Manager', 'Allows storing multiple tailored versions of resumes for different job roles'),
        ('Section-by-Section Score Breakdown', 'Detailed scorecards for Contact Info, Summary, Experience, Education, Projects'),
        ('Overused Cliché & Buzzword Detector', 'Flags filler phrases like hard working, team player, and detail oriented'),
        ('Grammar & Spelling Linter for Resumes', 'Detects typos, inconsistent capitalization, and tense mismatches'),
        ('One-Page Layout & Margin Enforcer', 'Warns if content spills onto awkward second pages and adjusts line height'),
        ('Downloadable LaTeX Source Code', 'Exports ready-to-compile Overleaf-compatible .tex source code'),
        ('Privacy Redaction Tool for Resumes', 'Automatically redacts phone numbers, addresses, and photos for blind screening'),
        ('Verified Credential & Project Link Checker', 'Verifies that GitHub, LinkedIn, and live project URLs are valid and reachable'),
        ('Resume Analytics (Views & Downloads)', 'Tracks how many times placement cells or recruiters viewed the resume'),
        ('Placement Cell Bulk Resume Downloader', 'Allows college admins to export zip files of approved student resumes'),
        ('Resume Review Feedback History', 'Logs historical comments and improvements across multiple iterations'),
        ('Sample Resumes of Placed Candidates', 'Curated gallery of anonymized resumes of students placed at top firms')
    ]),
    ('GITHUB', 'Module K: GitHub Intelligence', [
        ('OAuth GitHub Account Connector', 'Securely connects student GitHub profile with fine-grained read scopes'),
        ('Repository Quality & Health Scanner', 'Audits repositories for presence of README, License, tests, and documentation'),
        ('Language & Tech Stack Distribution Analyzer', 'Visual breakdown of primary languages across all student public repositories'),
        ('Commit Velocity & Consistency Tracker', 'Analyzes frequency, commit message quality, and active coding streaks'),
        ('README Documentation Grader', 'Scores README files on project description, architecture diagram, and setup steps'),
        ('Portfolio Readiness Benchmark', 'Scores student GitHub profile on 10 criteria for recruiter readiness'),
        ('Automated Skill Inference Engine', 'Infers verified technical skills directly from committed code files'),
        ('Project Originality & Fork Detector', 'Distinguishes between original repositories, cloned assignments, and tutorial copies'),
        ('Repository Security & Secret Exposure Checker', 'Flags committed .env files, API keys, or exposed credentials in public repos'),
        ('Top Pinned Repository Recommender', 'Suggests which 4 repositories best showcase the student skill set to recruiters'),
        ('Open Source Contribution Highlighter', 'Detects and highlights pull requests merged into external open source projects'),
        ('Automated Portfolio Website Generator', 'Generates clean, hosted personal portfolio page from GitHub metadata'),
        ('Project Complexity Metric Calculator', 'Estimates complexity based on directory depth, test coverage, and LOC'),
        ('Actionable Repository Improvement Checklist', 'Provides specific step-by-step PR suggestions to upgrade weak repositories'),
        ('GitHub Intelligence Exportable Report', 'Generates PDF report showcasing code maturity to placement officers'),
        ('Batch GitHub Analytics for Colleges', 'Allows placement cell to view aggregate GitHub commit stats across entire batch')
    ]),
    ('JOB', 'Module L: Job & Internship Intelligence', [
        ('Curated Job & Internship Board', 'Verified listings of entry-level engineering jobs, off-campus drives, and internships'),
        ('Smart Job-Skill Match Score', 'Computes percentage compatibility between student profile and job requirements'),
        ('Kanban Application Pipeline Tracker', 'Visual drag-and-drop board (Wishlist, Applied, OA, Interview, Offer, Rejected)'),
        ('Application Deadline Countdown & Calendar', 'Calendar view of application closing dates and assessment schedules'),
        ('Custom Job Alert Notifications', 'Email and in-app alerts matching student preferences and target CTC'),
        ('Saved Jobs & Opportunity Bookmark Queue', 'Allows saving jobs to review and apply later with notes'),
        ('Company Profile & Hiring History Dossier', 'In-depth profile covering tech stack, interview stages, and culture'),
        ('Off-Campus Drive Eligibility Verifier', 'Validates graduation year, degree, and percentage against drive requirements'),
        ('Direct Application Portal Links', 'Direct verified links to official company career portals (no ad redirects)'),
        ('Placement Drive Registration Flow', 'One-click registration for on-campus drives organized by college placement cell'),
        ('Salary & Compensation Comparison Tool', 'Compares base pay, stock options, and location benefits across job offers'),
        ('Application Note & Journal Feature', 'Personal diary to record notes, HR contacts, and interview impressions per job'),
        ('Hiring Trends & Skill Demand Analytics', 'Displays currently trending skills and hiring volume across tech industries'),
        ('Alumni Network at Company Finder', 'Highlights college alumni currently working at the hiring company'),
        ('Referral Request Message Drafter', 'Generates professional, polite LinkedIn outreach templates for referrals'),
        ('Job Listing Source & Provenance Badge', 'Displays data provenance (Official Campus, Career Page, Verified Partner)'),
        ('Stale Job Listing Auto-Archive', 'Automatically archives expired postings to prevent applying to dead roles'),
        ('Application Analytics & Funnel Conversion', 'Visual funnel showing conversion rate from application to interview to offer')
    ]),
    ('PLACE', 'Module M: Placement Cell Dashboard', [
        ('Institutional Dashboard Command Center', 'Overview of total students, eligible students, active drives, and placed count'),
        ('Student Roster & Academic Directory', 'Filterable student directory by department, CGPA, backlogs, and verification status'),
        ('Placement Eligibility Rule Engine', 'Sets custom filters (CGPA >= 7.5, 0 backlogs, CSE/ECE only) for drives'),
        ('Company Onboarding & Recruiter Portal', 'Manages corporate hiring partners, HR contacts, and partnership tiers'),
        ('Campus Drive Lifecycle Manager', 'Manages full drive workflow from announcement to test, shortlist, and final offers'),
        ('Student Application Approval Queue', 'Allows placement officers to verify and approve student applications for drives'),
        ('Shortlist & Selected Candidate Publisher', 'Publishes official round-wise shortlists and offer lists with notification alerts'),
        ('Automated Offer Letter Repository', 'Stores verified offer letters and tracks CTC and joining dates per student'),
        ('Department & Batch Placement Statistics', 'Generates department-wise placement percentages and average package charts'),
        ('Comprehensive CSV & Excel Data Exporter', 'Exports NIRF and NAAC compliant accreditation reports in one click'),
        ('Official Placement PDF Report Generator', 'Generates formatted institutional annual placement booklet in PDF'),
        ('Bulk Student Email & SMS Broadcast', 'Sends urgent drive updates and schedule changes to eligible student cohorts'),
        ('Company-Wise Historical Performance Report', 'Tracks hiring numbers and student feedback across visiting companies over years'),
        ('Student Opt-Out & Higher Studies Tracker', 'Categorizes students seeking higher education or opting out of campus drives'),
        ('Placement Officer Multi-User RBAC', 'Supports multiple placement coordinators with assigned departments and duties'),
        ('Company Interview Slot Scheduler', 'Coordinates on-campus or virtual interview slots between recruiters and students'),
        ('Student Disciplinary & Blacklist Manager', 'Temporarily debars students who violate placement policies or skip interviews'),
        ('Mock Drive Score Aggregator for TPO', 'Evaluates batch preparedness based on mock test and mock interview analytics'),
        ('Recruiter Feedback & Rating Collection', 'Collects structured feedback from company HR on candidate performance and curriculum'),
        ('Live Campus Drive Announcement Ticker', 'Real-time alert banner broadcasting urgent venue and schedule changes'),
        ('One-Offer / Dream-Offer Policy Enforcer', 'Enforces college policy restricting students after securing standard vs dream offers'),
        ('Placement Audit Trail & Activity Logger', 'Logs all officer actions, shortlists, and eligibility overrides for transparency')
    ]),
    ('ADMIN', 'Module N: Admin Intelligence', [
        ('Super Admin Central Command Console', 'High-level telemetry on active users, API traffic, database health, and errors'),
        ('User Management & Identity Directory', 'CRUD interface for managing student, admin, and placement officer accounts'),
        ('Role-Based Access Control (RBAC) Manager', 'Configures fine-grained permissions for custom administrative roles'),
        ('Question Bank Master Management', 'Reviews, approves, edits, and categorizes coding and assessment questions'),
        ('Company Catalog & Logo Manager', 'Curates company profiles, hiring patterns, domains, and brand assets'),
        ('System-Wide Feature Flags & Kill Switches', 'Toggles individual modules and features on or off without redeployment'),
        ('Audit Log & Security Event Explorer', 'Searchable audit trail tracking all privileged logins, updates, and deletes'),
        ('Platform Usage & Engagement Analytics', 'Daily active users, peak traffic hours, and popular learning tracks'),
        ('Content Moderation Queue for Discussions', 'Reviews flagged user comments, forum posts, and reported questions'),
        ('API Key & External Service Configuration', 'Secure interface for updating AI model keys and third-party webhook URLs'),
        ('Database Backup & Maintenance Controller', 'Initiates manual database backups and displays backup verification logs'),
        ('Error Tracking & Exception Inspector', 'Aggregates unhandled backend exceptions with stack traces and user impact'),
        ('Security Vulnerability & Suspicious Activity Scanner', 'Monitors brute-force login attempts, rapid API bursts, and SQLi signatures'),
        ('AI Model Cost & Token Telemetry Dashboard', 'Detailed cost breakdown by provider, endpoint, and user cohort'),
        ('Notification Dispatcher & Broadcast Center', 'Sends platform-wide system maintenance and update notifications'),
        ('System Health & Worker Heartbeat Monitor', 'Real-time ping monitor for backend API, database, cache, and sandbox worker'),
        ('Sandbox Execution Queue Monitor', 'Monitors code runner worker queue depth, execution times, and failure rates'),
        ('Platform Terms, Privacy & Compliance Editor', 'Updates and versions legal terms and GDPR/data privacy disclaimers'),
        ('Data Retention & Account Purge Automation', 'Configures retention lifecycles for logs, temp files, and deleted accounts'),
        ('System Diagnostic Report Generator', 'Exports full markdown/JSON diagnostic snapshot for engineering troubleshooting')
    ]),
    ('PEER', 'Module O: Peer Learning & Community', [
        ('Topic-Based Discussion Forums', 'Categorized community forums for Coding, Placement Doubts, and Core CS'),
        ('Question-Specific Doubt Threads', 'Embedded discussion section on every coding problem and assessment question'),
        ('Peer Study Groups & Circles', 'Allows students to create private or public study groups with chat and goal boards'),
        ('Community Upvoting & Best Answer Marker', 'Upvote helpful answers and award accepted answer checkmark to solutions'),
        ('Markdown & Code Block Community Editor', 'Full-featured text editor supporting syntax-highlighted code snippets'),
        ('Peer Solution Comparison Viewer', 'Allows comparing accepted solutions between peers after contest completion'),
        ('Collaborative Real-Time Study Notes', 'Shared notes document editable by members of a study group'),
        ('Peer Weekly Challenge Arena', 'Friendly 1-on-1 or group coding challenges with friends'),
        ('Community Reputation & Karma Points', 'Awards karma for helpful answers, bug reports, and quality explanations'),
        ('Toxic Language & Abuse Auto-Moderator', 'Automatically flags and hides abusive or spam comments using heuristics'),
        ('Study Group Goal Tracker & Leaderboard', 'Tracks shared progress on group milestones'),
        ('Virtual Study Room Pomodoro Timer', 'Synchronized timer for group study sessions with ambient focus sounds'),
        ('Peer Mentorship Connection Hub', 'Connects junior students with senior placed peers for informal guidance'),
        ('Discussion Search & Tag Filtering', 'Fuzzy search across community questions with tag filters'),
        ('User Profile Community Badges', 'Displays Top Contributor and Helpful Peer badges on forum comments'),
        ('Community Guidelines & Reporting Workflow', 'Clear conduct rules with one-click user reporting mechanism')
    ]),
    ('NOTIF', 'Module P: Notification Intelligence', [
        ('In-App Notification Center Drawer', 'Interactive dropdown showing unread alerts, timestamps, and action links'),
        ('Notification Preferences & Channel Toggles', 'Allows users to customize alert channels (In-App, Email, Push) per category'),
        ('Placement Drive Urgency Alerts', 'High-priority notifications for new job postings, shortlisted status, and drive deadlines'),
        ('Assessment & Test Schedule Reminders', 'Automated reminders 24h, 1h, and 15m prior to scheduled tests'),
        ('Daily Streak Loss Warning Alert', 'Evening reminder alert if student has not completed daily sprint task'),
        ('Spaced Repetition Review Due Notification', 'Notifies students when high-priority flashcards are due for review'),
        ('Peer Reply & Mention Notification', 'Alerts users when someone replies to their discussion thread or @mentions them'),
        ('Transactional Email Delivery Engine', 'Sends verification emails, password resets, and score receipts via SMTP/API'),
        ('Browser Web Push Notifications', 'Sends desktop push alerts via Service Workers when tab is in background'),
        ('Notification Delivery History & Audit', 'Logs status (sent, delivered, opened, failed) of all notifications'),
        ('Batch Notification Queue Worker', 'Asynchronous background worker that batches alerts to prevent rate limits'),
        ('Notification Snooze & Quiet Hours', 'Allows students to set quiet hours to mute non-urgent pings'),
        ('Custom Webhook Dispatcher for Colleges', 'Pushes placement announcements to institutional Discord or Slack channels'),
        ('Rich HTML Email Templates', 'Responsive cyber-themed email templates for weekly digests and certificates'),
        ('Unsubscribe & Notification Management Link', 'One-click unsubscribe links compliant with CAN-SPAM and privacy standards'),
        ('Real-Time WebSocket Notification Bus', 'Instant real-time badge updates without requiring page reload')
    ]),
    ('SEC', 'Module Q: Privacy & Security Controls', [
        ('Centralized JWT Authentication Engine', 'Access token (short-lived) and Refresh token (secure httpOnly) architecture'),
        ('Bcrypt Password Hashing & Salt Standard', 'Industry-standard password hashing with cost factor 12'),
        ('Strict Role-Based Authorization Guards', 'Decorators enforcing STUDENT, ADMIN, and PLACEMENT_CELL scopes on endpoints'),
        ('IDOR Protection Verification Layer', 'Validates that resource IDs belong to the requesting user before read/write'),
        ('Cross-Site Request Forgery (CSRF) Tokens', 'Protects mutating state endpoints against CSRF exploitation'),
        ('API Rate Limiting & Brute Force Defense', 'IP and user-based sliding window rate limiters on login and AI routes'),
        ('Input Sanitization & XSS Prevention', 'Sanitizes all user-submitted markdown and HTML to prevent stored XSS'),
        ('SQL Injection Prevention via ORM', 'Parameterized queries exclusively through SQLAlchemy ORM, no raw string interpolation'),
        ('Secure File Upload Validator', 'Strict MIME type checking, extension validation, and virus signature scanning'),
        ('HTTPS & Strict Transport Security (HSTS)', 'Enforces TLS encryption with HSTS, secure cookies, and no-sniff headers'),
        ('Content Security Policy (CSP) Headers', 'Restricts script, frame, and style origins to prevent injection attacks'),
        ('Granular User Privacy Settings', 'Allows students to hide profile, GPA, and GitHub from public peer views'),
        ('GDPR-Compliant Data Export Tool', 'Generates downloadable JSON archive of all personal data held on user'),
        ('Right to be Forgotten Account Deletion', 'Permanently deletes user account, anonymizes test attempts, and purges data'),
        ('Two-Factor Authentication (OTP via Email)', 'Optional email OTP layer for sensitive actions (password change, deletion)'),
        ('Session Revocation & Kill Switch', 'Allows logging out of all active devices and revoking all refresh tokens'),
        ('Security Audit Log & Tamper Detection', 'Append-only audit log recording all password resets, role changes, and admin logins'),
        ('Environment Secret Isolation', 'Loads all credentials from environment variables, strictly prohibiting hardcoding'),
        ('Dependency Vulnerability Audit Hook', 'Automated scanning pipeline checking npm audit and pip safety warnings'),
        ('Sandbox Escape & Isolation Defense', 'Ensures code execution worker runs unprivileged with zero kernel bypass vectors')
    ]),
    ('SYS', 'Module R: System Intelligence & Telemetry', [
        ('Unified /health/live Healthcheck Endpoint', 'Lightweight endpoint returning 200 OK indicating web process responsiveness'),
        ('Deep /health/ready Dependency Probe', 'Verifies database connectivity, cache reachability, and sandbox worker status'),
        ('Structured JSON Application Logger', 'Formats all logs with ISO timestamps, request IDs, log level, and user context'),
        ('Distributed Request ID Tracing Middleware', 'Attaches unique UUID to every incoming HTTP request for end-to-end tracing'),
        ('Automated Database Migration Verification', 'Checks Alembic migration heads on startup and blocks unmigrated launches'),
        ('Automated Database Backup Script', 'Generates timestamped PostgreSQL dumps with gzip compression and rotation'),
        ('Automated Disaster Recovery Test Script', 'Restores backup into isolated test database and verifies row count integrity'),
        ('Backend Performance & Slow Query Logger', 'Flags database queries and API routes exceeding 500ms execution time'),
        ('Background Worker Queue Heartbeat Monitor', 'Periodically pings asynchronous task runners and alerts on stalls'),
        ('Disk Space & Storage Threshold Watchdog', 'Monitors filesystem capacity and warns before disk fills above 85%'),
        ('Memory Leak & Process RSS Watcher', 'Monitors backend RAM footprint and alerts on memory leak growth'),
        ('Zero-Downtime Deployment Configuration', 'Graceful SIGTERM shutdown handling to finish in-flight requests'),
        ('Docker Compose Orchestration Stack', 'Production-ready docker-compose.yml defining API, DB, Sandbox, and Nginx'),
        ('Reverse Proxy & Nginx Configuration', 'Configures gzip compression, client body limits, SSL certificates, and routing'),
        ('Automated Seed Data Generator', 'Populates database with 100+ companies, 1,000+ problems, and demo cohorts'),
        ('Continuous Integration (CI) Test Runner', 'Automated shell/python script running unit, integration, and security test suites'),
        ('Production Build Verification Hook', 'Validates Next.js build and TypeScript types before release tagging'),
        ('System Architecture & Topology Diagram', 'Maintains up-to-date visual architecture documentation in Markdown/Mermaid')
    ])
]

feat_registry = """# NEXORA AI - Master Feature Registry (300+ Features)

> **Standard:** Every feature requirement is uniquely identified, specified with end-to-end requirements, acceptance criteria, test cases, and dependency mapping.
> **Total Identified Features:** 346 Features across 18 Core Modules.

---

"""

traceability = """# NEXORA AI - Feature Traceability Matrix

| Feature ID | Category | Module Name | Feature Title | Backend API | Database Models | Frontend Route / Component | Test Cases |
|---|---|---|---|---|---|---|---|
"""

status_doc = """# NEXORA AI - Feature Implementation Status

| Feature ID | Feature Title | Module | Phase | Status | Verification Gate |
|---|---|---|---|---|---|
"""

dependency_map = """# NEXORA AI - Feature Dependency Map

```mermaid
graph TD
    AUTH[FEAT-311: Centralized JWT Auth] --> RBAC[FEAT-313: RBAC Guards]
    RBAC --> STU_DASH[Module B: AI Career Copilot]
    RBAC --> ASSESS[Module C: Assessment Intelligence]
    RBAC --> CODING[Module D: Coding Arena]
    RBAC --> INTERVIEW[Module F: Interview Intelligence]
    RBAC --> PLACE[Module M: Placement Cell]
    RBAC --> ADMIN[Module N: Admin Intelligence]
    
    BRAIN[Module A: Unified AI Brain] --> COPILOT[Module B: AI Career Copilot]
    BRAIN --> CODEREV[Module E: AI Code Review]
    BRAIN --> INTERVIEW
    BRAIN --> RESUME[Module J: Resume Intelligence]
    
    CODING --> SANDBOX[FEAT-067: Process-Isolated Sandbox]
    CODING --> CODEREV
    
    ASSESS --> WEAK[FEAT-055: Weak Area Tag Extractor]
    WEAK --> REVISION[Module H: Smart Revision SM-2]
    
    RESUME --> JOB[Module L: Job Intelligence]
    GITHUB[Module K: GitHub Intelligence] --> JOB
    JOB --> PLACE
```

---

## Detailed Component Dependencies

"""

global_id = 1

for cat_code, cat_title, feats in modules:
    feat_registry += f"## {cat_title}\n\n"
    for name, desc in feats:
        fid = f"FEAT-{global_id:03d}"
        backend_req = "FastAPI endpoint with Pydantic validation, business service layer, and audit logging"
        db_req = "SQLAlchemy model with foreign key constraints, indexes, and migration tracking"
        fe_req = "Next.js responsive UI component matching Obsidian & Cyber Lime design tokens"
        api_req = f"/api/v1/{cat_code.lower()}/..."
        sec_req = "Enforce RBAC role verification, IDOR validation, and sanitized inputs"
        acc_crit = "Feature functions end-to-end with valid frontend, API response, DB persistence, and zero errors"
        tests = f"test_{cat_code.lower()}_{global_id:03d}"
        
        feat_registry += f"### {fid}: {name}\n"
        feat_registry += f"- **Category:** {cat_title}\n"
        feat_registry += f"- **Description:** {desc}\n"
        feat_registry += f"- **Frontend Requirements:** {fe_req}\n"
        feat_registry += f"- **Backend Requirements:** {backend_req}\n"
        feat_registry += f"- **Database Requirements:** {db_req}\n"
        feat_registry += f"- **API Requirements:** {api_req}\n"
        feat_registry += f"- **Security Requirements:** {sec_req}\n"
        feat_registry += f"- **Acceptance Criteria:** {acc_crit}\n"
        feat_registry += f"- **Test Cases:** `{tests}`\n"
        feat_registry += f"- **Status:** PLANNED\n"
        feat_registry += f"- **Dependencies:** FEAT-311 (Auth), FEAT-313 (RBAC)\n\n"
        
        module_short = cat_title.split(": ")[1]
        traceability += f"| {fid} | {cat_code} | {module_short} | {name} | `{api_req}` | `db_{cat_code.lower()}` | `/{cat_code.lower()}` | `{tests}` |\n"
        
        phase_map = {
            'BRAIN': 'Phase 6', 'COPILOT': 'Phase 6', 'ASSESS': 'Phase 7',
            'CODING': 'Phase 5', 'CODEREV': 'Phase 5', 'INTERVIEW': 'Phase 7',
            'LEARN': 'Phase 4', 'REVISION': 'Phase 10', 'DSAVIZ': 'Phase 4',
            'RESUME': 'Phase 8', 'GITHUB': 'Phase 8', 'JOB': 'Phase 8',
            'PLACE': 'Phase 9', 'ADMIN': 'Phase 9', 'PEER': 'Phase 10',
            'NOTIF': 'Phase 10', 'SEC': 'Phase 2 & 12', 'SYS': 'Phase 0, 1 & 12'
        }
        phase = phase_map.get(cat_code, 'Phase 3')
        status_doc += f"| {fid} | {name} | {cat_code} | {phase} | PLANNED | Pending Implementation Gate |\n"
        
        dependency_map += f"- **{fid} ({name}):** Requires FEAT-311, FEAT-313; Integrates with {cat_code} core service.\n"
        
        global_id += 1

os.makedirs('docs', exist_ok=True)

with open('docs/MASTER_FEATURE_REGISTRY.md', 'w', encoding='utf-8') as f:
    f.write(feat_registry)

with open('docs/FEATURE_TRACEABILITY_MATRIX.md', 'w', encoding='utf-8') as f:
    f.write(traceability)

with open('docs/FEATURE_IMPLEMENTATION_STATUS.md', 'w', encoding='utf-8') as f:
    f.write(status_doc)

with open('docs/FEATURE_DEPENDENCY_MAP.md', 'w', encoding='utf-8') as f:
    f.write(dependency_map)

print(f"Generated registries successfully for {global_id - 1} features.")
