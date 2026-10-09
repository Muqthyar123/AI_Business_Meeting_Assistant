import { Meeting, Transcript, Analysis, Decision, ActionItem, FollowUpPlan } from '../types';

export const INITIAL_DEMO_MEETINGS: Meeting[] = [
  {
    id: 'meet-101',
    title: 'Q4 Product Strategy & Roadmap Alignment',
    description: 'Quarterly review to prioritize core AI initiatives, deprecate legacy v1 endpoints, and align cross-functional engineering deliverables for November launch.',
    meetingDate: '2026-10-08T14:30:00Z',
    durationSeconds: 2840, // ~47 mins
    participants: ['Elena Rostova (VP Product)', 'David Chen (Lead Architect)', 'Sarah Jenkins (Eng Director)', 'Marcus Vance (PMM Lead)'],
    meetingType: 'Planning',
    department: 'Product & Engineering',
    status: 'ready',
    transcriptionId: 'trn-101',
    analysisStatus: 'completed',
    audioFilename: '2026-10-08_Q4_Roadmap_Review.mp3',
    createdAt: '2026-10-08T15:20:00Z',
    updatedAt: '2026-10-08T15:25:00Z',
  },
  {
    id: 'meet-102',
    title: 'Enterprise Client Architecture & Security Review',
    description: 'Technical deep dive with Apex Financial on SOC-2 compliance, on-premises LLM deployment latency requirements, and SLA agreements.',
    meetingDate: '2026-10-07T10:00:00Z',
    durationSeconds: 3120, // 52 mins
    participants: ['David Chen (Lead Architect)', 'Michael Sterling (Apex CTO)', 'Rachel Adams (Solutions Architect)', 'Amanda Cruz (Account Exec)'],
    meetingType: 'Client Meeting',
    department: 'Customer Success',
    status: 'ready',
    transcriptionId: 'trn-102',
    analysisStatus: 'completed',
    audioFilename: 'Apex_Architecture_Review_1007.wav',
    createdAt: '2026-10-07T11:05:00Z',
    updatedAt: '2026-10-07T11:12:00Z',
  },
  {
    id: 'meet-103',
    title: 'Sprint Retrospective & AI Tech Debt Triage',
    description: 'Bi-weekly engineering retro analyzing Whisper transcription memory leaks, LangGraph graph serialization issues, and Redis caching optimization.',
    meetingDate: '2026-10-06T16:00:00Z',
    durationSeconds: 2100, // 35 mins
    participants: ['Sarah Jenkins (Eng Director)', 'Alex Rivera (Backend Dev)', 'Priya Patel (ML Ops)', 'Tom Baker (QA Lead)'],
    meetingType: 'Team Meeting',
    department: 'Engineering',
    status: 'ready',
    transcriptionId: 'trn-103',
    analysisStatus: 'completed',
    audioFilename: 'Sprint_34_Retro_Audio.m4a',
    createdAt: '2026-10-06T16:45:00Z',
    updatedAt: '2026-10-06T16:50:00Z',
  },
  {
    id: 'meet-104',
    title: 'Executive Hiring & Leadership Compensation Committee',
    description: 'Confidential committee sync to review candidate pipelines for Principal AI Researcher and Head of Growth.',
    meetingDate: '2026-10-04T09:00:00Z',
    durationSeconds: 1860, // 31 mins
    participants: ['Elena Rostova (VP Product)', 'Arthur Vance (CEO)', 'Karen Miller (Head of People)'],
    meetingType: 'Interview',
    department: 'Executive',
    status: 'ready',
    transcriptionId: 'trn-104',
    analysisStatus: 'completed',
    audioFilename: 'Exec_Hiring_Review_Oct04.mp3',
    createdAt: '2026-10-04T09:40:00Z',
    updatedAt: '2026-10-04T09:45:00Z',
  },
];

export const INITIAL_DEMO_TRANSCRIPTS: Record<string, Transcript> = {
  'meet-101': {
    id: 'trn-101',
    meetingId: 'meet-101',
    filename: '2026-10-08_Q4_Roadmap_Review.mp3',
    fileSizeBytes: 42150000,
    language: 'English (en)',
    durationSeconds: 2840,
    status: 'completed',
    text: `Elena Rostova: Good afternoon everyone. Let's get straight into the agenda. We have four key objectives for Q4: finalizing the LangGraph workflow orchestrator, setting the hard deprecation date for the v1 legacy REST endpoints, locking in pricing tiers with Marcus's team, and ensuring SOC-2 audit compliance readiness before November 15th.

David Chen: On the LangGraph transition, we completed benchmark runs this morning. The multi-agent state management reduced hallucination rates by 38% compared to single-prompt chains. However, memory overhead during concurrent audio chunking is peaking around 3.2 GB on our worker nodes. We need to throttle concurrent transcriptions per container to a maximum of 4.

Sarah Jenkins: Agreed on the container limit. If we set the concurrency cap to 4 per worker, our existing Kubernetes cluster can comfortably absorb the projected peak load without auto-scaling spikes. I've already prepared the Helm chart values update.

Elena Rostova: Perfect. That brings us to decision item one: we officially freeze new features on the v1 API by October 20th and redirect all customer traffic to v2 by November 15th. Does anyone have blockers with that timeline?

Marcus Vance: Sales needs at least three weeks of clear migration documentation. If engineering can supply the updated OpenAPI spec by next Monday, October 13th, my team will create the customer communication sequence and release notes by October 18th.

David Chen: I can commit to finishing the OpenAPI schema and code samples by Monday evening. Alex on my team is already wrapping up the schema validation tests.

Elena Rostova: Excellent. Next, let's talk about the AI summary quality. A few beta enterprise customers noted that when meetings exceed 60 minutes, the executive summaries occasionally omit tactical decisions made in the final 10 minutes. 

David Chen: That was caused by our token chunking window truncating the tail end before the recursive summarizer kicked in. In our LangGraph rewrite, we implemented a map-reduce summarization graph that explicitly preserves the closing 15 minutes in a dedicated action-extraction node. That completely resolves the drop-off issue.

Sarah Jenkins: I will ensure QA runs verification test suites on 10 lengthy synthetic meeting recordings by this Friday to validate the fix.

Elena Rostova: Fantastic. To wrap up: David will finalize the OpenAPI spec by Monday, Sarah will deploy the worker concurrency limits and run QA regression suites, Marcus will draft the migration guide, and I will review the final November launch deck with Arthur on Thursday. Let's make this quarter count!`,
    segments: [
      { id: 'seg-1', start: 0, end: 18, speaker: 'Elena Rostova', text: 'Good afternoon everyone. Let\'s get straight into the agenda. We have four key objectives for Q4: finalizing the LangGraph workflow orchestrator, setting the hard deprecation date for v1 REST endpoints, locking in pricing tiers, and ensuring SOC-2 compliance.' },
      { id: 'seg-2', start: 19, end: 42, speaker: 'David Chen', text: 'On the LangGraph transition, multi-agent state management reduced hallucination rates by 38%. However, memory overhead during concurrent audio chunking is peaking around 3.2 GB. We need to throttle concurrency per worker container to 4.' },
      { id: 'seg-3', start: 43, end: 60, speaker: 'Sarah Jenkins', text: 'Agreed on the container limit. If we set concurrency to 4 per worker, our K8s cluster can comfortably absorb peak load without autoscaling spikes. Helm chart is ready.' },
      { id: 'seg-4', start: 61, end: 82, speaker: 'Elena Rostova', text: 'Decision one: we officially freeze new features on v1 API by October 20th and redirect all customer traffic to v2 by November 15th.' },
      { id: 'seg-5', start: 83, end: 105, speaker: 'Marcus Vance', text: 'Sales needs 3 weeks of migration documentation. If engineering supplies the OpenAPI spec by Monday October 13th, my team will publish customer communication by October 18th.' },
      { id: 'seg-6', start: 106, end: 122, speaker: 'David Chen', text: 'I commit to finishing the OpenAPI schema and code samples by Monday evening. Schema tests are nearly done.' },
      { id: 'seg-7', start: 123, end: 155, speaker: 'Elena Rostova', text: 'Next on summary quality: enterprise beta users noticed long meetings (>60 mins) omitted decisions in the final 10 minutes.' },
      { id: 'seg-8', start: 156, end: 182, speaker: 'David Chen', text: 'Resolved in LangGraph via a map-reduce graph preserving the closing 15 minutes in a dedicated action-extraction node.' },
      { id: 'seg-9', start: 183, end: 200, speaker: 'Sarah Jenkins', text: 'QA will run regression test suites on 10 lengthy recordings by Friday to validate the fix.' },
      { id: 'seg-10', start: 201, end: 230, speaker: 'Elena Rostova', text: 'Summary: David delivers OpenAPI specs Monday, Sarah deploys concurrency limits and runs QA, Marcus prepares migration docs, and I present the deck Thursday.' }
    ],
    createdAt: '2026-10-08T15:21:00Z',
    updatedAt: '2026-10-08T15:21:00Z',
  },
  'meet-102': {
    id: 'trn-102',
    meetingId: 'meet-102',
    filename: 'Apex_Architecture_Review_1007.wav',
    fileSizeBytes: 54200000,
    language: 'English (en)',
    durationSeconds: 3120,
    status: 'completed',
    text: `Michael Sterling: Thank you David and Rachel for hosting this session. Apex Financial handles high volumes of sensitive executive earnings calls. Our primary requirements are zero-data-retention on audio binaries once transcribed, maximum 2.5 second p99 latency for summary generation, and complete SOC-2 Type II audit logs.

David Chen: Understood Michael. In our hybrid deployment model, all audio decoding and Whisper inference runs completely inside your VPC or isolated tenant pod. The audio payload is held in volatile memory only and never written to disk. As soon as the transcription vector is created, the RAM buffer is wiped.

Rachel Adams: Furthermore, we support customer-managed encryption keys via AWS KMS or Azure Key Vault, guaranteeing that MeetMind engineers cannot access unencrypted transcript fragments.

Michael Sterling: That matches our strict compliance standard. What about the Groq inference gateway? Does Groq retain prompt tokens?

David Chen: We operate on Groq's Enterprise Dedicated Instance tier under a signed BAA/DPA with strict zero-data-retention (ZDR). Neither Groq nor MeetMind trains models on your transcript data.

Michael Sterling: That is exactly what our compliance team needed to hear. Let's agree to schedule the 14-day technical pilot kickoff for October 19th. Rachel, can you send over the Terraform scripts and architecture blueprint by this Thursday?

Rachel Adams: Yes, I will deliver the validated Terraform scripts and deployment guide by Thursday October 9th end of day.`,
    createdAt: '2026-10-07T11:06:00Z',
    updatedAt: '2026-10-07T11:06:00Z',
  },
  'meet-103': {
    id: 'trn-103',
    meetingId: 'meet-103',
    filename: 'Sprint_34_Retro_Audio.m4a',
    fileSizeBytes: 29800000,
    language: 'English (en)',
    durationSeconds: 2100,
    status: 'completed',
    text: `Sarah Jenkins: Welcome everyone to the Sprint 34 Retro. Let's start with what went well: the Groq Llama 3 70B inference latency dropped from 850ms to 240ms after moving to structured JSON output parsing. What didn't go well: we encountered three transient timeouts when processing audio files over 150MB.

Priya Patel: The root cause was synchronous FFmpeg normalization in the upload FastAPI handler. When two users simultaneously uploaded large FLAC recordings, worker CPU pegged at 100% and delayed transcription handoff.

Alex Rivera: We should decouple audio ingestion from FFmpeg conversion using a Celery/Redis background queue with streaming chunking. That way the HTTP response returns immediately with a task ID.

Sarah Jenkins: Let's make that our top technical debt priority for Sprint 35. Alex, take ownership of the async audio preprocessing queue. Priya, will you configure the Prometheus alerts for worker CPU saturation?

Priya Patel: Absolutely. I'll configure alerting thresholds at 80% sustained CPU for 3 minutes.`,
    createdAt: '2026-10-06T16:46:00Z',
    updatedAt: '2026-10-06T16:46:00Z',
  },
  'meet-104': {
    id: 'trn-104',
    meetingId: 'meet-104',
    filename: 'Exec_Hiring_Review_Oct04.mp3',
    fileSizeBytes: 22100000,
    language: 'English (en)',
    durationSeconds: 1860,
    status: 'completed',
    text: `Arthur Vance: Elena, Karen, thanks for meeting. We need to close our Principal AI Researcher search this month. We have two finalist candidates: Dr. Aris Thorne from DeepMind and Dr. Meera Rao from Anthropic.

Karen Miller: Both candidates cleared technical interviews with flying colors. Dr. Thorne has stronger expertise in structured state-space models, whereas Dr. Rao has unparalleled experience in long-context retrieval and agentic evaluation frameworks.

Elena Rostova: Given our Q4 push toward autonomous meeting action execution and LangGraph multi-agent workflows, Dr. Rao's background aligns directly with our immediate 12-month technical roadmap.

Arthur Vance: I agree. Let's prepare a formal offer package for Dr. Rao. Karen, please align with the comp committee on equity grants and present the offer by Wednesday.`,
    createdAt: '2026-10-04T09:41:00Z',
    updatedAt: '2026-10-04T09:41:00Z',
  },
};

export const INITIAL_DEMO_ANALYSES: Record<string, Analysis> = {
  'meet-101': {
    id: 'ans-101',
    meetingId: 'meet-101',
    summary: 'The leadership team aligned on key Q4 priorities, deciding to enforce a hard feature freeze on v1 APIs on October 20 and complete customer transition to v2 by November 15. Container concurrency for transcription was capped at 4 to resolve memory bottlenecks, and a map-reduce summarization fix was validated to eliminate summary drop-offs in long meetings.',
    purpose: 'Quarterly roadmap alignment, architectural bottleneck remediation, and API deprecation milestone scheduling.',
    keyPoints: [
      'LangGraph multi-agent architecture reduced hallucination rates by 38% in comparative benchmarks.',
      'Worker node memory overhead was diagnosed at 3.2 GB during peak concurrency; resolved by setting a hard limit of 4 concurrent transcriptions per container.',
      'API v1 hard deprecation agreed for November 15, with feature freeze taking effect on October 20.',
      'OpenAPI specifications and migration guide scheduled for release by October 13 to allow customer communication by October 18.',
      'Resolved summarization truncation in >60 minute meetings using dedicated action-extraction map-reduce nodes.',
    ],
    topics: ['LangGraph Architecture', 'API Deprecation', 'Container Optimization', 'Customer Migration', 'QA Verification'],
    risks: [
      'Customer pushback on the November 15 migration deadline if OpenAPI documentation is delayed past October 13.',
      'Potential memory spikes if unexpected spike in concurrent long audio uploads occurs before Helm update is deployed.',
    ],
    openQuestions: [
      'Will legacy webhook integrations receive automated backward-compatibility shims during the transition window?',
      'Has the partner tier been informed of potential token rate limits under the v2 architecture?',
    ],
    suggestedNextSteps: [
      'Deploy Helm chart concurrency throttling to staging and production clusters.',
      'Finalize OpenAPI 3.1 documentation and publish developer sandbox by Monday.',
      'Run QA automated test harness against 10 long-format audio recordings.',
      'Schedule customer notification emails starting October 18.',
    ],
    status: 'completed',
    modelUsed: 'Groq Llama-3.3-70b-versatile via LangGraph',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  'meet-102': {
    id: 'ans-102',
    meetingId: 'meet-102',
    summary: 'Apex Financial agreed to commence a 14-day technical pilot on October 19th after validating MeetMind’s zero-data-retention (ZDR) architecture, in-memory volatile audio handling, and Groq enterprise enterprise BAA agreements.',
    purpose: 'Enterprise security, compliance review, and architecture clearance for pilot deployment.',
    keyPoints: [
      'Confirmed zero disk persistence for raw audio binaries; buffers are flushed from volatile memory immediately post-vectorization.',
      'Supported customer-managed KMS encryption keys for tenant isolation.',
      'Groq confirmed zero-data-retention compliance under signed BAA agreement.',
      'Agreed 14-day technical pilot kick-off target date of October 19th.',
    ],
    topics: ['Enterprise Security', 'SOC-2 Compliance', 'Zero Data Retention', 'KMS Encryption', 'Pilot Kickoff'],
    risks: [
      'Apex firewall configurations may require custom VPC peering routes during pilot deployment.',
    ],
    openQuestions: [
      'Does Apex require on-premise Whisper fallback in case of regional cloud egress degradation?',
    ],
    suggestedNextSteps: [
      'Deliver verified Terraform deployment scripts by October 9th.',
      'Provide signed Groq BAA and SOC-2 Type II audit report package to Apex legal.',
    ],
    status: 'completed',
    modelUsed: 'Groq Llama-3.3-70b-versatile via LangGraph',
    createdAt: '2026-10-07T11:08:00Z',
    updatedAt: '2026-10-07T11:08:00Z',
  },
  'meet-103': {
    id: 'ans-103',
    meetingId: 'meet-103',
    summary: 'Identified root cause of upload timeouts on audio files >150MB as synchronous FFmpeg processing in FastAPI handler. Agreed to implement an asynchronous Celery/Redis queue in Sprint 35.',
    purpose: 'Sprint 34 retrospective and audio processing technical debt triage.',
    keyPoints: [
      'Inference latency reduced by 72% (to 240ms) using structured JSON output parsing.',
      'Synchronous FFmpeg transcoding identified as the single bottleneck causing worker CPU spikes.',
      'Agreed to decouple upload ingestion from transcoding via Redis task queue.',
    ],
    topics: ['Sprint Retro', 'FFmpeg Transcoding', 'Redis Task Queue', 'CPU Monitoring', 'Latency Optimization'],
    risks: ['Redis memory pressure if large queue of unprocessed files accumulates.'],
    openQuestions: ['Should we introduce chunked streaming upload directly to S3/MinIO?'],
    suggestedNextSteps: ['Create Celery worker task for async FFmpeg audio conversion.', 'Set up Prometheus alerting for CPU saturation >80%.'],
    status: 'completed',
    modelUsed: 'Groq Llama-3.3-70b-versatile via LangGraph',
    createdAt: '2026-10-06T16:48:00Z',
    updatedAt: '2026-10-06T16:48:00Z',
  },
  'meet-104': {
    id: 'ans-104',
    meetingId: 'meet-104',
    summary: 'Executive committee finalized selection of Dr. Meera Rao for the Principal AI Researcher position due to direct alignment with agentic systems and multi-agent roadmaps.',
    purpose: 'Executive hiring decision and candidate compensation alignment.',
    keyPoints: [
      'Evaluated two finalist candidates: Dr. Aris Thorne and Dr. Meera Rao.',
      'Selected Dr. Rao based on extensive background in multi-agent evaluation and long-context reasoning.',
      'Authorized HR to prepare and present comprehensive equity package by Wednesday.',
    ],
    topics: ['Executive Hiring', 'AI Research', 'Talent Acquisition', 'Compensation'],
    risks: ['Competing offers from other frontier AI labs.'],
    openQuestions: ['What start date will accommodate Dr. Rao’s existing research transition?'],
    suggestedNextSteps: ['Present finalized offer letter and equity package to Dr. Rao by Wednesday.'],
    status: 'completed',
    modelUsed: 'Groq Llama-3.3-70b-versatile via LangGraph',
    createdAt: '2026-10-04T09:43:00Z',
    updatedAt: '2026-10-04T09:43:00Z',
  },
};

export const INITIAL_DEMO_DECISIONS: Decision[] = [
  {
    id: 'dec-201',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Cap container concurrency at 4 audio transcriptions per worker',
    description: 'Enforce a strict concurrency ceiling of 4 active audio streams per Kubernetes worker pod to prevent memory spikes above 3.2 GB.',
    owner: 'Sarah Jenkins',
    status: 'Confirmed',
    category: 'Infrastructure',
    evidence: 'If we set the concurrency cap to 4 per worker, our existing Kubernetes cluster can comfortably absorb the projected peak load without auto-scaling spikes.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'dec-202',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Freeze v1 API features by Oct 20; full cutover to v2 by Nov 15',
    description: 'Halt all feature additions to legacy v1 endpoints on October 20th and complete full customer redirection to v2 by November 15th.',
    owner: 'Elena Rostova',
    status: 'Confirmed',
    category: 'Product Roadmap',
    evidence: 'Decision item one: we officially freeze new features on the v1 API by October 20th and redirect all customer traffic to v2 by November 15th.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'dec-203',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Adopt Map-Reduce summarization node for long meetings',
    description: 'Use LangGraph map-reduce graph with an explicit closing-segment action item extraction node to ensure 60+ minute calls retain final decisions.',
    owner: 'David Chen',
    status: 'Confirmed',
    category: 'AI Architecture',
    evidence: 'In our LangGraph rewrite, we implemented a map-reduce summarization graph that explicitly preserves the closing 15 minutes in a dedicated action-extraction node.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'dec-204',
    meetingId: 'meet-102',
    meetingTitle: 'Enterprise Client Architecture & Security Review',
    title: 'Schedule Apex Financial 14-day pilot kickoff for Oct 19',
    description: 'Commence enterprise pilot deployment under zero-data-retention parameters following security and legal clearance.',
    owner: 'Rachel Adams',
    status: 'Confirmed',
    category: 'Customer Success',
    evidence: 'Let\'s agree to schedule the 14-day technical pilot kickoff for October 19th.',
    createdAt: '2026-10-07T11:08:00Z',
    updatedAt: '2026-10-07T11:08:00Z',
  },
  {
    id: 'dec-205',
    meetingId: 'meet-103',
    meetingTitle: 'Sprint Retrospective & AI Tech Debt Triage',
    title: 'Migrate synchronous FFmpeg transcoding to async Redis queue',
    description: 'Decouple file upload endpoint from media transcoding by introducing an asynchronous Celery/Redis task queue.',
    owner: 'Alex Rivera',
    status: 'Confirmed',
    category: 'Technical Debt',
    evidence: 'We should decouple audio ingestion from FFmpeg conversion using a Celery/Redis background queue with streaming chunking.',
    createdAt: '2026-10-06T16:48:00Z',
    updatedAt: '2026-10-06T16:48:00Z',
  },
  {
    id: 'dec-206',
    meetingId: 'meet-104',
    meetingTitle: 'Executive Hiring & Leadership Compensation Committee',
    title: 'Extend formal offer to Dr. Meera Rao for Principal AI Researcher',
    description: 'Extend competitive principal-level compensation package including specialized equity vesting.',
    owner: 'Karen Miller',
    status: 'Confirmed',
    category: 'Hiring',
    evidence: 'Let\'s prepare a formal offer package for Dr. Rao. Karen, please align with the comp committee on equity grants and present the offer by Wednesday.',
    createdAt: '2026-10-04T09:43:00Z',
    updatedAt: '2026-10-04T09:43:00Z',
  },
];

export const INITIAL_DEMO_ACTION_ITEMS: ActionItem[] = [
  {
    id: 'act-301',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Finalize OpenAPI 3.1 specification and migration code samples',
    description: 'Generate full OAS 3.1 schema definitions for v2 endpoints and sample cURL / TypeScript code snippets for customers.',
    assignee: 'David Chen',
    assigneeEmail: 'david.chen@meetmind.ai',
    dueDate: '2026-10-13T23:59:00Z',
    priority: 'High',
    status: 'In Progress',
    evidence: 'I can commit to finishing the OpenAPI schema and code samples by Monday evening.',
    notes: 'Alex is wrapping up test fixtures.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'act-302',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Deploy worker concurrency limits to Kubernetes Helm config',
    description: 'Update staging and production Helm values to enforce MAX_CONCURRENT_TRANSCRIPTIONS=4 per pod.',
    assignee: 'Sarah Jenkins',
    assigneeEmail: 'sarah.jenkins@meetmind.ai',
    dueDate: '2026-10-10T18:00:00Z',
    priority: 'Urgent',
    status: 'To Do',
    evidence: 'I\'ve already prepared the Helm chart values update.',
    notes: 'Requires coordination with DevOps for non-disruptive rolling restart.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'act-303',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Publish customer migration guide and deprecation notice sequence',
    description: 'Prepare email sequences, docs.meetmind.ai deprecation banners, and step-by-step upgrade guides.',
    assignee: 'Marcus Vance',
    assigneeEmail: 'marcus.vance@meetmind.ai',
    dueDate: '2026-10-18T17:00:00Z',
    priority: 'Medium',
    status: 'To Do',
    evidence: 'Sales needs at least three weeks of clear migration documentation... my team will create the customer communication sequence by October 18th.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'act-304',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Run automated QA regression harness on 10 long (>60min) audio calls',
    description: 'Verify that the new map-reduce node in LangGraph correctly extracts decisions from final 15 minutes of audio.',
    assignee: 'Sarah Jenkins',
    assigneeEmail: 'sarah.jenkins@meetmind.ai',
    dueDate: '2026-10-10T17:00:00Z',
    priority: 'High',
    status: 'In Progress',
    evidence: 'I will ensure QA runs verification test suites on 10 lengthy synthetic meeting recordings by this Friday to validate the fix.',
    createdAt: '2026-10-08T15:23:00Z',
    updatedAt: '2026-10-08T15:23:00Z',
  },
  {
    id: 'act-305',
    meetingId: 'meet-102',
    meetingTitle: 'Enterprise Client Architecture & Security Review',
    title: 'Send validated Terraform deployment scripts to Apex Financial',
    description: 'Deliver AWS VPC Terraform templates with KMS customer-managed key configuration and validation docs.',
    assignee: 'Rachel Adams',
    assigneeEmail: 'rachel.adams@meetmind.ai',
    dueDate: '2026-10-09T20:00:00Z',
    priority: 'Urgent',
    status: 'In Progress',
    evidence: 'I will deliver the validated Terraform scripts and deployment guide by Thursday October 9th end of day.',
    createdAt: '2026-10-07T11:08:00Z',
    updatedAt: '2026-10-07T11:08:00Z',
  },
  {
    id: 'act-306',
    meetingId: 'meet-103',
    meetingTitle: 'Sprint Retrospective & AI Tech Debt Triage',
    title: 'Configure Prometheus alerting for worker CPU >80% sustained',
    description: 'Setup Prometheus alert rule with Slack channel webhook when worker node CPU exceeds 80% for 3 continuous minutes.',
    assignee: 'Priya Patel',
    assigneeEmail: 'priya.patel@meetmind.ai',
    dueDate: '2026-10-12T18:00:00Z',
    priority: 'Medium',
    status: 'Completed',
    evidence: 'I\'ll configure alerting thresholds at 80% sustained CPU for 3 minutes.',
    createdAt: '2026-10-06T16:48:00Z',
    updatedAt: '2026-10-08T10:15:00Z',
  },
  {
    id: 'act-307',
    meetingId: 'meet-104',
    meetingTitle: 'Executive Hiring & Leadership Compensation Committee',
    title: 'Present formal offer package to Dr. Meera Rao',
    description: 'Deliver finalized offer letter with approved equity grant structure and start date options.',
    assignee: 'Karen Miller',
    assigneeEmail: 'karen.miller@meetmind.ai',
    dueDate: '2026-10-08T18:00:00Z',
    priority: 'Urgent',
    status: 'Completed',
    evidence: 'Karen, please align with the comp committee on equity grants and present the offer by Wednesday.',
    createdAt: '2026-10-04T09:43:00Z',
    updatedAt: '2026-10-08T16:00:00Z',
  },
];

export const INITIAL_DEMO_FOLLOW_UPS: FollowUpPlan[] = [
  {
    id: 'flw-401',
    meetingId: 'meet-101',
    meetingTitle: 'Q4 Product Strategy & Roadmap Alignment',
    title: 'Q4 API v2 Transition & Architecture Hardening Plan',
    objective: 'Successfully deprecate v1 endpoints, transition all active customer traffic to v2, and stabilize cluster memory overhead prior to November 15 launch.',
    keyOutcomes: [
      'Zero production memory crashes during peak ingestion hours',
      '100% of tier-1 customers migrated to v2 before November 15',
      'Automated QA pipeline validating long-meeting transcript extraction',
    ],
    steps: [
      {
        id: 'step-1',
        stepNumber: 1,
        title: 'Deploy worker concurrency limits to Kubernetes',
        description: 'Cap concurrency per container to 4 to stabilize RAM usage under 3.2 GB.',
        suggestedTiming: 'By Oct 10',
        owner: 'Sarah Jenkins',
        status: 'pending',
        relatedActionItemId: 'act-302',
      },
      {
        id: 'step-2',
        stepNumber: 2,
        title: 'Run QA automated tests on 10 long recordings',
        description: 'Confirm map-reduce action extraction resolves truncation in 60+ min meetings.',
        suggestedTiming: 'By Oct 10',
        owner: 'Sarah Jenkins',
        status: 'pending',
        relatedActionItemId: 'act-304',
      },
      {
        id: 'step-3',
        stepNumber: 3,
        title: 'Publish OpenAPI 3.1 specification & code samples',
        description: 'Provide developer-ready schemas for client teams.',
        suggestedTiming: 'By Oct 13',
        owner: 'David Chen',
        status: 'pending',
        relatedActionItemId: 'act-301',
      },
      {
        id: 'step-4',
        stepNumber: 4,
        title: 'Release customer migration documentation & deprecation sequence',
        description: 'Announce 3-week transition window to all API consumers.',
        suggestedTiming: 'By Oct 18',
        owner: 'Marcus Vance',
        status: 'pending',
        relatedActionItemId: 'act-303',
      },
      {
        id: 'step-5',
        stepNumber: 5,
        title: 'Enforce v1 API feature freeze',
        description: 'Lock v1 codebase to security fixes only.',
        suggestedTiming: 'By Oct 20',
        owner: 'David Chen',
        status: 'pending',
      },
      {
        id: 'step-6',
        stepNumber: 6,
        title: 'Complete 100% cutover of production traffic to v2',
        description: 'Final deprecation of legacy routes and decommission old workers.',
        suggestedTiming: 'By Nov 15',
        owner: 'Elena Rostova',
        status: 'pending',
      },
    ],
    risks: [
      'Customer migration friction or delayed integration updates on client side',
      'Unanticipated cluster load if batch uploads coincide during migration week',
    ],
    checkInDates: ['2026-10-14', '2026-10-21', '2026-11-04', '2026-11-14'],
    status: 'Active',
    createdAt: '2026-10-08T15:24:00Z',
    updatedAt: '2026-10-08T15:24:00Z',
  },
  {
    id: 'flw-402',
    meetingId: 'meet-102',
    meetingTitle: 'Enterprise Client Architecture & Security Review',
    title: 'Apex Financial 14-Day Pilot Implementation Plan',
    objective: 'Deploy isolated VPC sandbox, validate zero-data-retention compliance, and verify p99 inference latency under 2.5 seconds.',
    keyOutcomes: [
      'Signed security audit sign-off from Apex CISO',
      'Successful end-to-end transcription and Groq analysis in customer VPC',
      'Transition to production enterprise contract',
    ],
    steps: [
      {
        id: 'step-201',
        stepNumber: 1,
        title: 'Deliver Terraform scripts and KMS configuration',
        description: 'Provide automated deployment files to Apex DevOps.',
        suggestedTiming: 'By Oct 9',
        owner: 'Rachel Adams',
        status: 'pending',
        relatedActionItemId: 'act-305',
      },
      {
        id: 'step-202',
        stepNumber: 2,
        title: 'Kick off technical sandbox installation',
        description: 'Joint pairing session to deploy tenant pod.',
        suggestedTiming: 'Oct 19',
        owner: 'David Chen & Apex Team',
        status: 'pending',
      },
      {
        id: 'step-203',
        stepNumber: 3,
        title: 'Execute zero-data-retention audit verification',
        description: 'Verify memory wipe behavior with Apex security auditor.',
        suggestedTiming: 'Oct 24',
        owner: 'Rachel Adams',
        status: 'pending',
      },
    ],
    risks: ['Apex internal proxy firewalls blocking WebSocket telemetry'],
    checkInDates: ['2026-10-15', '2026-10-22', '2026-10-31'],
    status: 'Active',
    createdAt: '2026-10-07T11:10:00Z',
    updatedAt: '2026-10-07T11:10:00Z',
  },
];
