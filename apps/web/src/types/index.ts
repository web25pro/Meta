// User Types
export enum UserRole {
  OVERALL_ADMIN = 'Overall_Admin',
  AMBASSADOR_ADMIN = 'Ambassador_Admin',
  TEAM_MEMBER = 'Team_Member',
  AMBASSADOR = 'Ambassador',
  USER = 'User',
}

export enum UserType {
  TEAM_MEMBER = 'Team_Member',
  AMBASSADOR = 'Ambassador',
  USER = 'User',
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  user_type: UserType;
  points: number;
  created_at: string;
  updated_at: string;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Task Types
export enum AssignedGroup {
  TEAM_MEMBERS = 'Team_Members',
  AMBASSADORS = 'Ambassadors',
  ALL = 'All',
}

export interface Task {
  id: string;
  title: string;
  description: string;
  assigned_to_group: AssignedGroup;
  deadline: string;
  point_value: number;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description: string;
  assigned_to_group: AssignedGroup;
  deadline: string;
  point_value: number;
}

// Submission Types
export enum SubmissionStatus {
  PENDING = 'Pending',
  APPROVED = 'Approved',
  REJECTED = 'Rejected',
}

export interface Submission {
  id: string;
  task_id: string;
  user_id: string;
  content: string;
  status: SubmissionStatus;
  submitted_at: string;
  reviewed_by_id?: string;
  reviewed_at?: string;
  files: SubmissionFile[];
}

export interface SubmissionFile {
  id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  scan_status: string;
  created_at: string;
}

export interface SubmissionCreate {
  task_id: string;
  content: string;
}

// Points Types
export enum TransactionType {
  TASK_APPROVAL = 'Task_Approval',
  DEADLINE_PENALTY = 'Deadline_Penalty',
  ADMIN_BONUS = 'Admin_Bonus',
  ADMIN_PENALTY = 'Admin_Penalty',
}

export interface PointsTransaction {
  id: string;
  user_id: string;
  amount: number;
  transaction_type: TransactionType;
  reason: string;
  related_task_id?: string;
  related_submission_id?: string;
  created_at: string;
}

export interface UserPoints {
  user_id: string;
  points: number;
  rank?: number;
}

// Leaderboard Types
export interface LeaderboardEntry {
  user_id: string;
  user_name: string;
  rank: number;
  total_pp: number;
  user_type: UserType;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
  page: number;
  page_size: number;
}

// Schedule Types
export interface Schedule {
  id: string;
  title: string;
  description: string;
  event_date: string;
  target_group: AssignedGroup;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface ScheduleCreate {
  title: string;
  description: string;
  event_date: string;
  target_group: AssignedGroup;
}

// Announcement Types
export interface Announcement {
  id: string;
  title: string;
  content: string;
  target_group: AssignedGroup;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface AnnouncementCreate {
  title: string;
  content: string;
  target_group: AssignedGroup;
}

// Pagination Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// API Error Types
export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, any>;
  };
}

// Dashboard Types
export interface DashboardStats {
  total_tasks: number;
  pending_submissions: number;
  total_points: number;
  current_rank: number;
  tasks_completed: number;
  tasks_pending: number;
}
