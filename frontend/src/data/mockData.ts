// Mock data for RFQ Generator Agent

export interface RFQ {
  id: string;
  reference: string;
  title: string;
  category: string;
  status: 'draft' | 'in_review' | 'approved' | 'sent';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  team: string;
  relevanceScore?: number;
  sourceDocument?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: string;
  team: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sources?: { name: string; relevance: number }[];
  isTyping?: boolean;
}

export interface AgentState {
  phase: 'idle' | 'plan' | 'retrieve' | 'draft' | 'review' | 'analyze';
  progress: number;
}

export interface DocumentSource {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'xlsx';
  relevanceScore: number;
  category: string;
  uploadedAt: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: string;
  read: boolean;
}

// Current user
export const currentUser: User = {
  id: 'user-001',
  name: 'sundar',
  email: 'sundar@stellantis.com',
  avatar: '',
  role: 'Senior Procurement Manager',
  team: 'Powertrain & EV Systems',
};

// Recently generated RFQs
export const recentRFQs: RFQ[] = [
  {
    id: 'rfq-001',
    reference: 'RFQ-2025-BAT-009',
    title: 'HV Battery Pack - STLA Medium Platform',
    category: 'EV Components',
    status: 'draft',
    createdAt: '2025-12-30T14:30:00Z',
    updatedAt: '2025-12-30T16:45:00Z',
    createdBy: 'Sarah Mitchell',
    team: 'Powertrain & EV Systems',
    relevanceScore: 98,
    sourceDocument: 'RFQ_Jeep_GC_Battery_2023.pdf',
  },
  {
    id: 'rfq-002',
    reference: 'RFQ-2025-MOT-015',
    title: 'Electric Drive Unit - 180kW',
    category: 'EV Components',
    status: 'in_review',
    createdAt: '2025-12-28T09:15:00Z',
    updatedAt: '2025-12-29T11:20:00Z',
    createdBy: 'Sarah Mitchell',
    team: 'Powertrain & EV Systems',
    relevanceScore: 94,
    sourceDocument: 'RFQ_EDU_2024.pdf',
  },
  {
    id: 'rfq-003',
    reference: 'RFQ-2025-CHG-003',
    title: 'Onboard Charger Module - 22kW',
    category: 'EV Components',
    status: 'approved',
    createdAt: '2025-12-20T10:00:00Z',
    updatedAt: '2025-12-27T14:30:00Z',
    createdBy: 'Sarah Mitchell',
    team: 'Powertrain & EV Systems',
    relevanceScore: 91,
  },
  {
    id: 'rfq-004',
    reference: 'RFQ-2025-TMS-007',
    title: 'Thermal Management System - Battery Cooling',
    category: 'Climate Control',
    status: 'sent',
    createdAt: '2025-12-15T13:45:00Z',
    updatedAt: '2025-12-22T09:00:00Z',
    createdBy: 'Sarah Mitchell',
    team: 'Powertrain & EV Systems',
    relevanceScore: 89,
  },
  {
    id: 'rfq-005',
    reference: 'RFQ-2025-BMS-012',
    title: 'Battery Management System Software',
    category: 'Software',
    status: 'draft',
    createdAt: '2025-12-29T08:00:00Z',
    updatedAt: '2025-12-29T08:00:00Z',
    createdBy: 'Sarah Mitchell',
    team: 'Powertrain & EV Systems',
  },
];

// Historical document sources
export const documentSources: DocumentSource[] = [
  {
    id: 'doc-001',
    name: 'RFQ_Jeep_GC_Battery_2023.pdf',
    type: 'pdf',
    relevanceScore: 98,
    category: 'EV Components',
    uploadedAt: '2023-06-15T10:00:00Z',
  },
  {
    id: 'doc-002',
    name: 'RFQ_EDU_2024.pdf',
    type: 'pdf',
    relevanceScore: 94,
    category: 'EV Components',
    uploadedAt: '2024-02-20T14:30:00Z',
  },
  {
    id: 'doc-003',
    name: 'Global_Battery_Safety_Std_v4.docx',
    type: 'docx',
    relevanceScore: 85,
    category: 'Compliance',
    uploadedAt: '2024-08-10T09:15:00Z',
  },
  {
    id: 'doc-004',
    name: 'Supplier_Evaluation_Template.xlsx',
    type: 'xlsx',
    relevanceScore: 76,
    category: 'Templates',
    uploadedAt: '2024-01-05T11:45:00Z',
  },
  {
    id: 'doc-005',
    name: 'RFQ_TMS_Cooling_2024.pdf',
    type: 'pdf',
    relevanceScore: 89,
    category: 'Climate Control',
    uploadedAt: '2024-04-12T16:00:00Z',
  },
  {
    id: 'doc-006',
    name: 'EV_Procurement_Guidelines_2025.pdf',
    type: 'pdf',
    relevanceScore: 92,
    category: 'Compliance',
    uploadedAt: '2025-01-10T08:30:00Z',
  },
];

// Sample chat conversation
export const sampleConversation: ChatMessage[] = [
  {
    id: 'msg-001',
    role: 'assistant',
    content: "Hello Sarah! I'm ready to help you draft a new Request for Quotation. What would you like to create today?",
    timestamp: '2025-12-30T14:00:00Z',
  },
  {
    id: 'msg-002',
    role: 'user',
    content: 'Generate an RFQ for Tier 1 Battery Packs for the upcoming STLA Medium platform. Use the 2023 Jeep Grand Cherokee battery RFQ as a template but update the capacity to 98kWh.',
    timestamp: '2025-12-30T14:01:00Z',
  },
  {
    id: 'msg-003',
    role: 'assistant',
    content: "I'll create an RFQ for HV Battery Packs based on your specifications. Let me retrieve relevant documents and draft the content.",
    timestamp: '2025-12-30T14:01:30Z',
    sources: [
      { name: 'RFQ_Jeep_GC_Battery_2023.pdf', relevance: 98 },
      { name: 'Global_Battery_Safety_Std_v4.docx', relevance: 85 },
    ],
  },
];

// Notifications
export const notifications: Notification[] = [
  {
    id: 'notif-001',
    title: 'RFQ Approved',
    message: 'RFQ-2025-CHG-003 has been approved by the legal team.',
    type: 'success',
    timestamp: '2025-12-30T10:30:00Z',
    read: false,
  },
  {
    id: 'notif-002',
    title: 'Review Required',
    message: 'RFQ-2025-MOT-015 is pending your review.',
    type: 'warning',
    timestamp: '2025-12-29T16:00:00Z',
    read: false,
  },
  {
    id: 'notif-003',
    title: 'New Document Uploaded',
    message: 'EV_Procurement_Guidelines_2025.pdf has been added to the knowledge base.',
    type: 'info',
    timestamp: '2025-12-28T09:00:00Z',
    read: true,
  },
];

// Dashboard stats
export const dashboardStats = {
  totalRFQs: 156,
  thisMonth: 12,
  pendingReview: 3,
  approved: 8,
  averageGenerationTime: '45 seconds',
  knowledgeBaseDocuments: 1247,
};

// Sample generated RFQ content
export const sampleRFQContent = {
  reference: 'RFQ-2025-BAT-009',
  date: 'December 15, 2025',
  title: 'Request for Quotation: HV Battery Pack',
  sections: [
    {
      id: 'exec-summary',
      title: 'Executive Summary',
      content: `Stellantis is inviting qualified Tier 1 suppliers to submit proposals for the design, development, and manufacturing of High Voltage (HV) Battery Packs for the STLA Medium platform. The target capacity is 98kWh with a focus on high energy density and fast-charging capabilities.`,
      confidence: 95,
      sourceRFQ: 'RFQ_Jeep_GC_Battery_2023.pdf',
    },
    {
      id: 'scope',
      title: 'Scope of Work',
      content: `The supplier shall provide a complete turnkey solution including:
• Cell-to-Pack module assembly
• Thermal Management System (TMS) integration
• Battery Management System (BMS) hardware and software
• All necessary testing and validation per Stellantis standards`,
      confidence: 92,
      sourceRFQ: 'RFQ_Jeep_GC_Battery_2023.pdf',
    },
    {
      id: 'tech-specs',
      title: 'Technical Specifications',
      content: `| Parameter | Requirement |
|-----------|-------------|
| Energy Capacity | 98 kWh (Usable) |
| Voltage Architecture | 400V (Option for 800V) |
| Chemistry | NMC 811 |
| Fast Charging | 10-80% in 25 minutes |
| Cycle Life | >1000 cycles at 80% DoD |`,
      confidence: 98,
      sourceRFQ: 'RFQ_Jeep_GC_Battery_2023.pdf',
    },
    {
      id: 'compliance',
      title: 'Compliance & Warranty',
      content: `All components must adhere to the Global Battery Safety Standard v4 (Retrieved from Internal Docs). Warranty coverage shall extend to 8 years or 160,000 km, guaranteeing 70% state of health (SoH).`,
      confidence: 88,
      sourceRFQ: 'Global_Battery_Safety_Std_v4.docx',
    },
  ],
};

// Team members for collaboration
export const teamMembers: User[] = [
  currentUser,
  {
    id: 'user-002',
    name: 'Michael Chen',
    email: 'michael.chen@stellantis.com',
    avatar: '',
    role: 'Procurement Analyst',
    team: 'Powertrain & EV Systems',
  },
  {
    id: 'user-003',
    name: 'Emily Rodriguez',
    email: 'emily.rodriguez@stellantis.com',
    avatar: '',
    role: 'Legal Counsel',
    team: 'Legal',
  },
  {
    id: 'user-004',
    name: 'David Kim',
    email: 'david.kim@stellantis.com',
    avatar: '',
    role: 'Engineering Lead',
    team: 'Powertrain & EV Systems',
  },
];

// Categories for filtering
export const categories = [
  'All Categories',
  'EV Components',
  'Climate Control',
  'Software',
  'Compliance',
  'Templates',
  'IT Hardware',
  'Automotive Parts',
];

// Status options
export const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'in_review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'sent', label: 'Sent' },
];
