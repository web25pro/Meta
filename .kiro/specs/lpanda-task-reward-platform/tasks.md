# Implementation Plan: LPanda Meta-Jungle Task & Reward Management Platform

## Overview

This implementation plan breaks down the LPanda platform into discrete, manageable Python (FastAPI) development tasks. The architecture uses PostgreSQL for persistence, Redis for caching and job queues, and AWS S3 for file storage. Each task builds incrementally on previous work, with property-based tests validating core business logic.

## Tasks

- [x] 1. Project Setup and Infrastructure
  - Initialize FastAPI project structure with Poetry/pip
  - Configure PostgreSQL connection pooling and migrations (Alembic)
  - Set up Redis client for caching and job queues
  - Configure AWS S3 client for file uploads
  - Set up logging with structured JSON output
  - Configure environment variables and secrets management
  - _Requirements: 1.1, 2.1, 3.1_


- [x] 2. Database Schema and Models
  - [x] 2.1 Create core SQLAlchemy models (users, tasks, task_assignments)
    - Define User model with role, type, and PP balance fields
    - Define Task model with deadline and point value fields
    - Define TaskAssignment model for task-to-user mapping
    - _Requirements: 1.1, 2.1, 2.4_

  - [x] 2.2 Create submission and file storage models
    - Define TaskSubmission model with statuskiro .
     tracking
    - Define SubmissionFile model for file associations
    - Create database indexes for efficient queries
    - _Requirements: 3.1, 3.4, 11.1_

  - [x] 2.3 Create points transaction and audit models
    - Define PointsTransaction model for immutable transaction log
    - Define AuditLog model for administrative action tracking
    - Define DeadlinePenaltyApplied model for idempotency
    - _Requirements: 4.4, 5.6, 12.5_

  - [x] 2.4 Create leaderboard, schedule, and announcement models
    - Define LeaderboardCache model for fast queries
    - Define Schedule model with group targeting
    - Define Announcement model with visibility filtering
    - _Requirements: 6.1, 7.1, 8.1_

  - [ ]* 2.5 Write property tests for database models
    - **Property 4: Task Data Persistence**
    - **Property 36: User Profile Data Persistence**
    - **Validates: Requirements 2.4, 9.5**

- [x] 3. Authentication and Authorization System
  - [x] 3.1 Implement JWT token generation and validation
    - Create JWT token generation with 15-minute access token expiration
    - Implement token refresh with 7-day refresh token expiration
    - Store refresh tokens in Redis with secure HTTP-only cookies
    - _Requirements: 1.1, 1.2_

  - [x] 3.2 Implement password hashing and reset functionality
    - Use bcrypt with 12 salt rounds for password hashing
    - Implement password reset token generation (1-hour expiration)
    - Create password reset endpoint with validation
    - _Requirements: 1.1_

  - [x] 3.3 Implement Role-Based Access Control (RBAC) middleware
    - Create middleware to enforce role permissions on all endpoints
    - Implement permission matrix for Overall_Admin, Ambassador_Admin, Team_Member, Ambassador
    - Create decorators for role-based endpoint protection
    - _Requirements: 1.3, 1.4, 1.5, 1.6_

  - [x] 3.4 Implement session management with concurrent session limits
    - Store active sessions in Redis with 24-hour TTL
    - Enforce 3 concurrent session limit per user
    - Implement automatic logout on suspicious activity
    - _Requirements: 1.1, 1.2_

  - [ ]* 3.5 Write property tests for RBAC enforcement
    - **Property 1: Role-Based Access Control Enforcement**
    - **Validates: Requirements 1.3, 1.5, 1.6**

- [x] 4. User Management Module
  - [x] 4.1 Implement user creation and profile management
    - Create endpoint for user registration with validation
    - Implement user profile update endpoint
    - Create user listing endpoint with pagination (admin only)
    - _Requirements: 9.1, 9.2, 9.5_

  - [x] 4.2 Implement user deletion and password reset
    - Create user deletion endpoint with cascade handling
    - Implement password reset request and confirmation flow
    - Create admin password reset endpoint
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 4.3 Implement user type classification and validation
    - Validate user_type field contains only "Team_Member" or "Ambassador"
    - Create user type filtering for admin operations
    - Implement user type-based permission checks
    - _Requirements: 9.4, 9.5_

  - [ ]* 4.4 Write property tests for user management
    - **Property 33: Overall Admin User Management**
    - **Property 34: Ambassador Admin User Management Restriction**
    - **Property 35: User Type Classification**
    - **Validates: Requirements 9.1, 9.2, 9.4**

- [x] 5. Task Management Module
  - [x] 5.1 Implement task creation with scope enforcement
    - Create task creation endpoint with deadline requirement
    - Enforce assignment scope based on admin role (Overall_Admin vs Ambassador_Admin)
    - Validate task title, description, deadline, and point value
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 5.2 Implement task assignment to users and groups
    - Create TaskAssignment records for assigned users
    - Implement group-based assignment (Team_Members, Ambassadors)
    - Create endpoint to list assigned tasks for current user
    - _Requirements: 2.1, 2.2, 2.6_

  - [x] 5.3 Implement task update and deletion
    - Create task update endpoint with permission checks
    - Implement task deletion with cascade to assignments and submissions
    - Remove deleted tasks from user dashboards
    - _Requirements: 2.5, 2.6_

  - [x] 5.4 Implement task retrieval and filtering
    - Create endpoint to list all tasks (admin only)
    - Create endpoint to get task details
    - Implement pagination and filtering by status
    - _Requirements: 2.1, 2.4_

  - [ ]* 5.5 Write property tests for task management
    - **Property 2: Task Assignment Scope Enforcement**
    - **Property 3: Task Deadline Requirement**
    - **Property 5: Task Deletion Cascades**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6**

- [x] 6. Task Submission System
  - [x] 6.1 Implement task submission creation
    - Create submission endpoint accepting text, links, and file uploads
    - Set initial submission status to "Pending"
    - Enforce one submission per task per user
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 6.2 Implement submission status transitions
    - Create approval endpoint to transition submission to "Approved"
    - Create rejection endpoint to transition submission to "Rejected"
    - Validate status transitions and enforce admin-only access
    - _Requirements: 3.6_

  - [x] 6.3 Implement submission retrieval and listing
    - Create endpoint to get submission details
    - Create endpoint to list submissions for a task (admin only)
    - Create endpoint to list user's own submissions
    - _Requirements: 3.1, 3.2_

  - [ ]* 6.4 Write property tests for submission system
    - **Property 6: Submission Content Acceptance**
    - **Property 7: Single Submission Per Task Per User**
    - **Property 8: Submission Initial Status**
    - **Property 9: Submission Status Transitions**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

- [x] 7. File Upload and Storage System
  - [x] 7.1 Implement file upload validation
    - Validate file types against whitelist (PDF, DOCX, XLSX, PNG, JPG, GIF)
    - Validate individual file size (max 50MB) and submission total (max 200MB)
    - Implement MIME type verification
    - _Requirements: 11.2_

  - [x] 7.2 Implement S3  file storage integration
    - Generate presigned POST URLs for client-side uploads
    - Create submission_files records after successful upload
    - Implement file key generation with unique identifiers
    - _Requirements: 11.1, 11.3_

  - [x] 7.3 Implement file retrieval and access control
    - Generate presigned GET URLs (15-minute expiration) for downloads
    - Enforce permission checks for file access
    - Create endpoint to list files for a submission
    - _Requirements: 11.4, 11.5_

  - [x] 7.4 Implement virus scanning integration
    - Integrate ClamAV for malware detection
    - Create background job to scan uploaded files
    - Update submission_files with scan_status
    - Alert admin on malware detection
    - _Requirements: 11.3_

  - [ ]* 7.5 Write property tests for file upload system
    - **Property 37: File Upload Storage**
    - **Property 38: File Type Validation**
    - **Property 39: File Size Validation**
    - **Property 40: File Submission Association**
    - **Property 41: Admin File Access**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [x] 8. Points System and Rewards Engine
  - [x] 8.1 Implement points transaction logging
    - Create PointsTransaction records for all PP changes
    - Implement transaction types: Task_Approval, Deadline_Penalty, Admin_Bonus, Admin_Penalty
    - Create endpoint to retrieve user's transaction history
    - _Requirements: 5.6_

  - [x] 8.2 Implement task approval rewards
    - Award 50 PP for Team_Member task approvals
    - Award 138.6 PP for Ambassador task approvals
    - Create PointsTransaction record on approval
    - Prevent duplicate rewards for same submission
    - _Requirements: 5.1, 5.2, 5.7_

  - [x] 8.3 Implement admin bonus and penalty operations
    - Create endpoint for admin to award custom bonus points
    - Create endpoint for admin to apply custom penalty points
    - Create PointsTransaction records for all operations
    - _Requirements: 5.4, 5.5_

  - [x] 8.4 Implement user PP balance retrieval
    - Create endpoint to get current user's PP balance
    - Create endpoint to get any user's PP balance (admin only)
    - Implement efficient balance calculation from transactions
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x]* 8.5 Write property tests for points system
    - **Property 12: Team Member Reward Calculation**
    - **Property 13: Ambassador Reward Calculation**
    - **Property 14: Deadline Penalty Calculation**
    - **Property 15: Admin Bonus Points**
    - **Property 16: Admin Penalty Points**
    - **Property 17: Points Transaction History Completeness**
    - **Property 18: Reward Allocation Idempotency**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

- [x] 9. Leaderboard System
  - [x] 9.1 Implement leaderboard cache management
    - Create LeaderboardCache table with user_id, rank, total_pp, user_type
    - Implement cache refresh job running every 10 minutes
    - Calculate rankings in descending order by total_pp
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 9.2 Implement leaderboard retrieval endpoints
    - Create endpoint to get Team_Member leaderboard with pagination
    - Create endpoint to get Ambassador leaderboard with pagination
    - Create endpoint to get specific user's rank
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 9.3 Implement leaderboard segregation
    - Enforce user_type filtering in all leaderboard queries
    - Prevent cross-type mixing in results
    - Validate user_type values
    - _Requirements: 6.1_

  - [x] 9.4 Write property tests for leaderboard system
    - **Property 19: Leaderboard Segregation**
    - **Property 20: Leaderboard Ranking Correctness**
    - **Property 21: Leaderboard Position Update**
    - **Validates: Requirements 6.1, 6.2, 6.4**

- [x] 10. Schedule Management System
  - [x] 10.1 Implement schedule creation with scope enforcement
    - Create schedule creation endpoint with deadline and event_date fields
    - Enforce target_group scope based on admin role
    - Validate target_group values (Team_Members, Ambassadors, All)
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 10.2 Implement schedule update and deletion
    - Create schedule update endpoint with permission checks
    - Create schedule deletion endpoint
    - Implement soft delete for audit trail
    - _Requirements: 7.4_

  - [x] 10.3 Implement schedule retrieval with visibility filtering
    - Create endpoint to list schedules for current user
    - Filter schedules by user_type and target_group
    - Create admin endpoint to list all schedules
    - _Requirements: 7.1, 7.5, 7.6_

  - [x] 10.4 Implement read-only access enforcement
    - Enforce non-admin users cannot modify schedules
    - Return permission error on modification attempts
    - _Requirements: 7.6_

  - [ ]* 10.5 Write property tests for schedule system
    - **Property 22: Schedule Segregation**
    - **Property 23: Overall Admin Schedule Creation**
    - **Property 24: Ambassador Admin Schedule Restriction**
    - **Property 25: Schedule Modification**
    - **Property 26: Schedule Visibility Filtering**
    - **Property 27: Non-Admin Schedule Read-Only Access**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**

- [x] 11. Announcement System
  - [x] 11.1 Implement announcement creation with scope enforcement
    - Create announcement creation endpoint with title and content
    - Enforce target_group scope based on admin role
    - Validate target_group values (Team_Members, Ambassadors, All)
    - _Requirements: 8.1, 8.2_

  - [x] 11.2 Implement announcement update and deletion
    - Create announcement update endpoint with permission checks
    - Create announcement deletion endpoint (soft delete)
    - Maintain created_at for chronological ordering
    - _Requirements: 8.5_

  - [x] 11.3 Implement announcement retrieval with visibility filtering
    - Create endpoint to list announcements for current user
    - Filter announcements by user_type and target_group
    - Order results by created_at descending (newest first)
    - _Requirements: 8.3, 8.4_

  - [x] 11.4 Implement admin announcement listing
    - Create admin endpoint to list all announcements
    - Implement pagination for large result sets
    - _Requirements: 8.1, 8.2_

  - [ ]* 11.5 Write property tests for announcement system
    - **Property 28: Overall Admin Announcement Targeting**
    - **Property 29: Ambassador Admin Announcement Restriction**
    - **Property 30: Announcement Visibility Filtering**
    - **Property 31: Announcement Chronological Ordering**
    - **Property 32: Announcement Persistence**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [x] 12. Checkpoint - Core Modules Complete
  - Ensure all tests pass for authentication, user management, tasks, submissions, and points
  - Verify database schema is properly migrated
  - Ask the user if questions arise.


- [x] 18. Security and Audit Logging
  - [x] 18.1 Implement comprehensive audit logging
    - Log all administrative actions (create, update, delete)
    - Include admin_user_id, action, resource_type, resource_id, timestamp
    - Store in immutable audit_logs table
    - _Requirements: 12.5_

  - [x] 18.2 Implement request/response logging
    - Log all API requests with user_id, endpoint, method, status
    - Exclude sensitive data (passwords, tokens)
    - Implement log rotation and retention (2 years)
    - _Requirements: 12.5_

  - [x] 18.3 Implement error tracking and alerting
    - Integrate with error tracking service (Sentry)
    - Alert on error rate > 1%
    - Alert on response time p95 > 1 second
    - _Requirements: 12.2_

  - [x] 18.4 Implement rate limiting
    - Implement API rate limiting (100 requests/minute per user)
    - Implement file upload rate limiting (10 uploads/minute per user)
    - Implement leaderboard query rate limiting (30 requests/minute per user)
    - _Requirements: 1.1_

- [x] 19. Checkpoint - Background Jobs and Real-Time Complete
  - Ensure deadline enforcement job runs successfully
  - Verify leaderboard cache updates correctly
  - Test WebSocket connections and broadcasts
  - Ask the user if questions arise.


- [x] 20. API Documentation and Error Handling
  - [x] 20.1 Implement OpenAPI/Swagger documentation
    - Generate OpenAPI schema from FastAPI endpoints
    - Document all request/response schemas
    - Include authentication requirements and error codes
    - _Requirements: 1.1, 2.1_

  - [x] 20.2 Implement standardized error responses
    - Create error response format with code, message, details
    - Implement HTTP status codes (400, 401, 403, 404, 409, 422, 429, 500, 503)
    - Include validation error details in 422 responses
    - _Requirements: 1.1_

  - [x] 20.3 Implement request validation
    - Validate all request payloads against schemas
    - Return 422 with field-level error details
    - Implement custom validators for business logic
    - _Requirements: 1.1_

- [x] 21. Testing Infrastructure
  - [x] 21.1 Set up unit testing framework
    - Configure pytest with fixtures for database and Redis
    - Create test database with migrations
    - Implement test data factories
    - _Requirements: 1.1_

  - [x] 21.2 Set up integration testing
    - Create test client for API endpoints
    - Implement end-to-end test scenarios
    - Test role-based access control across endpoints
    - _Requirements: 1.1_

  - [x] 21.3 Set up property-based testing
    - Configure Hypothesis for property-based tests
    - Create strategies for generating test data
    - Implement property tests for all correctness properties
    - _Requirements: 1.1_

  - [x] 21.4 Set up performance testing
    - Configure load testing tools (locust or k6)
    - Create load test scenarios for 1000 concurrent users
    - Measure API response times and database performance
    - _Requirements: 1.1_

- [x] 22. Deployment and DevOps
  - [x] 22.1 Create Docker configuration
    - Create Dockerfile for FastAPI application
    - Create docker-compose.yml for local development
    - Include PostgreSQL, Redis, and S3 (MinIO) services
    - _Requirements: 1.1_

  - [x] 22.2 Create Kubernetes manifests
    - Create deployment manifests for production
    - Configure auto-scaling based on CPU/memory
    - Set up health checks and readiness probes
    - _Requirements: 1.1_

  - [x] 22.3 Implement CI/CD pipeline
    - Configure GitHub Actions for automated testing
    - Implement build and push to container registry
    - Set up automated deployment to staging
    - _Requirements: 1.1_

  - [x] 22.4 Implement monitoring and alerting
    - Configure Prometheus for metrics collection
    - Set up Grafana dashboards for visualization
    - Configure alerts for error rate, response time, job queue depth
    - _Requirements: 12.2, 12.3_

- [x] 23. Database Backup and Disaster Recovery
  - [x] 23.1 Implement backup strategy
    - Configure daily PostgreSQL snapshots
    - Set up 30-day retention policy
    - Implement cross-region replication for S3
    - _Requirements: 1.1_

  - [x] 23.2 Implement disaster recovery procedures
    - Document RTO (1 hour) and RPO (1 hour) procedures
    - Test backup restoration process
    - Create runbooks for common failure scenarios
    - _Requirements: 1.1_

- [x] 24. Final Integration and Testing
  - [x] 24.1 Implement end-to-end test scenarios
    - Test complete task submission workflow
    - Test deadline enforcement with multiple users
    - Test leaderboard updates with concurrent operations
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 24.2 Implement security testing
    - Test SQL injection prevention
    - Test XSS prevention
    - Test CSRF protection
    - Test authentication bypass attempts
    - Test authorization enforcement
    - _Requirements: 1.1_

  - [x] 24.3 Implement performance testing
    - Run load tests with 1000 concurrent users
    - Measure API response times (target: p95 < 1 second)
    - Verify database query performance
    - Verify WebSocket connection stability
    - _Requirements: 1.1_

- [x] 25. Checkpoint - All Systems Integrated
  - Ensure all tests pass (unit, integration, property-based, performance)
  - Verify all endpoints are documented in OpenAPI
  - Verify all requirements are covered by implementation
  - Ask the user if questions arise.

- [x] 26. Documentation and Knowledge Transfer
  - [x] 26.1 Create API documentation
    - Document all endpoints with examples
    - Document authentication and authorization
    - Document error codes and troubleshooting
    - _Requirements: 1.1_

  - [x] 26.2 Create deployment documentation
    - Document deployment procedures
    - Document environment configuration
    - Document monitoring and alerting setup
    - _Requirements: 1.1_

  - [x] 26.3 Create operational runbooks
    - Document common operational tasks
    - Document troubleshooting procedures
    - Document incident response procedures
    - _Requirements: 1.1_

- [x] 27. Final Checkpoint - Ready for Production
  - All tests passing with >80% coverage
  - All documentation complete and reviewed
  - All security requirements verified
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for feedback
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Implementation uses Python with FastAPI framework
- Database: PostgreSQL with SQLAlchemy ORM
- Caching: Redis for sessions, leaderboard cache, and job queues
- File Storage: AWS S3 with presigned URLs
- Real-time: Socket.io with Redis adapter for horizontal scaling
- Background Jobs: APScheduler or Celery for recurring tasks
