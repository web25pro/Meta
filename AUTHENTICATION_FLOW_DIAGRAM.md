# Complete Community Authentication Flow

## 1. Registration Flow

```
User → Register Page
  ↓
  • Enter email
  • Enter username
  • Enter password (validated: 8+ chars, uppercase, lowercase, digit)
  • Optional: enter referral code
  • Accept terms
  ↓
communityAPI.register() → Backend: POST /community/register
  ↓
Backend creates user with:
  • email
  • username
  • hashed password
  • referral_code (if provided)
  • email_verified: false
  ↓
Redirect → Check Email Page
  ↓
User receives email with verification link:
  • URL: /verify-email?token=...
  • Link expires in 24 hours
```

## 2. Email Verification Flow

```
User clicks verification link in email
  ↓
/verify-email?token=xyz123
  ↓
Verify Email Page:
  • Extracts token from URL
  • Shows loading state
  ↓
communityAPI.verifyEmail(token) → Backend: POST /community/verify-email
  ↓
Backend:
  • Validates token
  • Updates user.email_verified = true
  • Returns success
  ↓
Frontend:
  • Shows success message
  • Auto-redirects to /login after 2 seconds
  ↓
User can now login
```

## 3. Login Flow

```
User → Login Page
  ↓
  • Enter email
  • Enter password
  ↓
communityAPI.communityLogin(email, password)
  → Backend: POST /community/login
  ↓
Backend:
  • Validates email & password
  • Generates JWT token with iat (issued at)
  • Returns access_token & refresh_token
  ↓
Frontend:
  • Stores tokens in localStorage
  • Stores user info
  • Redirects to /dashboard
```

## 4. Password Reset Flow (Request)

```
User → Password Reset Page
  ↓
  • Enter email address
  ↓
communityAPI.requestPasswordReset(email)
  → Backend: POST /community/request-password-reset
  ↓
Backend:
  • Finds user by email
  • Generates password reset token
  • Sends email with link: /password-reset-confirm?token=...
  ↓
Frontend shows success message:
  "Check your email for reset link"
```

## 5. Password Reset Flow (Confirm)

```
User clicks reset link in email
  ↓
/password-reset-confirm?token=xyz456
  ↓
Password Reset Confirm Page:
  • Extracts token from URL
  • Shows password form
  ↓
User enters:
  • New password (validated)
  • Confirm password
  ↓
communityAPI.confirmPasswordReset({ token, new_password })
  → Backend: POST /community/confirm-password-reset
  ↓
Backend:
  • Validates token
  • Hashes new password
  • Updates user.password
  • Sets user.password_changed_at = now()
  • Invalidates all existing sessions
  ↓
Frontend:
  • Shows success message
  • Auto-redirects to /login after 2 seconds
  ↓
User must login with new password
```

## 6. Session Invalidation on Password Change

```
Old JWT Token (issued before password reset):
  {
    sub: user_id,
    email: user@example.com,
    iat: 1234567890,  // issued before password reset
    exp: 1234654290
  }

When user makes API request with old token:
  ↓
Backend get_current_user validates token:
  if user.password_changed_at > iat:
    → Return 401 Unauthorized (session invalid)
  else:
    → Allow request (session still valid)

Result: User must login again with new password
```

## 7. Dashboard Flow

```
After successful login
  ↓
Redirected to: /dashboard
  ↓
Dashboard Layout wraps all pages:
  • Sidebar with navigation
  • Main content area
  ↓
Available pages:
  • /dashboard (Overview)
  • /dashboard/community/profile (Stats & info)
  • /dashboard/community/referrals (Share link, stats)
  • /dashboard/community/settings (Account management)
  ↓
All pages:
  • Check authentication via useAuth()
  • If not authenticated → Redirect to /login
  • Display user-specific data
```

## 8. Referral Flow

```
Authenticated User → Referrals Page
  ↓
Frontend fetches:
  • communityAPI.getReferralCode()
  ↓
Backend returns:
  {
    referral_code: "REF_ABC123",
    total_referrals: 2,
    successful_referrals: 1,
    referral_earnings: 500
  }
  ↓
Referral Link displayed:
  • https://localhost:3000/register?ref=REF_ABC123
  ↓
Sharing options:
  • Copy to clipboard
  • Share on Twitter/Facebook/LinkedIn
  • Email link
  ↓
When friend uses referral link:
  • Adds ?ref=REF_ABC123 to URL
  • Registration page reads referral code
  • User enters: email, username, password, ref code
  • Both users get 500 points after new user verifies email
```

## 9. Protected Routes Flow

```
Dashboard pages require authentication:

Page load → useAuth() hook
  ↓
  if (user === null) {
    → Redirect to /login
  } else {
    → Render page content
  }

All dashboard pages protected:
  • /dashboard
  • /dashboard/community/profile
  • /dashboard/community/referrals
  • /dashboard/community/settings
```

## 10. Error Handling Flow

```
API Request Error:
  ↓
  if (error.response?.status === 401) {
    → Unauthorized (token expired/invalid)
    → Redirect to /login
  } else if (error.response?.status === 400) {
    → Validation error
    → Display error message in toast
    → Keep user on page, allow retry
  } else if (error.response?.status === 500) {
    → Server error
    → Display "Something went wrong" toast
    → Suggest contacting support
  }

Form Validation Error:
  ↓
  • Display error message below field
  • Disable submit button
  • Highlight field with red border
  • Show specific error reason
```

## State Management

### Global State (AuthContext)
```typescript
{
  user: {
    id: string,
    email: string,
    username?: string,
    email_verified?: boolean
  },
  isLoading: boolean,
  logout: () => void
}
```

### Local State (Per Component)
```typescript
// Register Page
- showPassword: boolean
- showConfirm: boolean
- isLoading: boolean

// Dashboard
- stats: CommunityUserStats
- isLoading: boolean

// Referrals
- referralData: ReferralData
- isLoading: boolean
- copied: boolean
```

## Component Hierarchy

```
RootLayout
  └── Providers
      ├── QueryClientProvider
      ├── AuthProvider
      │   └── (All pages inherit auth context)
      └── Toaster (for toast notifications)

Authentication Pages
  ├── RegisterPage (uses communityAPI.register)
  ├── CheckEmailPage (post-registration)
  ├── VerifyEmailPage (uses communityAPI.verifyEmail)
  ├── PasswordResetPage (uses communityAPI.requestPasswordReset)
  ├── PasswordResetConfirmPage (uses communityAPI.confirmPasswordReset)
  ├── ResendVerificationPage (uses communityAPI.resendVerificationEmail)
  └── LoginPage

Dashboard Pages (Protected by useAuth)
  └── DashboardLayout
      ├── Sidebar Navigation
      └── Main Content
          ├── DashboardPage (overview)
          ├── ProfilePage
          ├── ReferralsPage
          └── SettingsPage
```

## API Endpoints Summary

| Endpoint | Method | Request | Response | Purpose |
|----------|--------|---------|----------|---------|
| `/community/register` | POST | email, username, password, referral_code | user_id, token | Create account |
| `/community/verify-email` | POST | token | success | Verify email |
| `/community/resend-verification-email` | POST | email | success | Resend link |
| `/community/request-password-reset` | POST | email | success | Request reset |
| `/community/confirm-password-reset` | POST | token, new_password | success | Complete reset |
| `/community/login` | POST | email, password | access_token, refresh_token | Login |
| `/community/referral-code` | GET | - | referral_code, stats | Get referral info |

## Security Measures

1. **Frontend Validation**
   - Email format validation
   - Password strength requirements
   - Username format validation
   - Referral code format validation

2. **Token Management**
   - Access tokens stored in localStorage
   - Refresh tokens stored in localStorage
   - Tokens included in Authorization headers
   - 401 response triggers redirect to login

3. **Session Invalidation**
   - `password_changed_at` field tracks password changes
   - Old tokens rejected if issued before password reset
   - Automatic logout on password change
   - Users must re-login after password reset

4. **Protected Routes**
   - Dashboard pages check authentication
   - Redirect unauthenticated users to login
   - Cannot access protected pages without token

## Responsive Design Breakpoints

```
Mobile (< 768px)
  └── Stack layout vertically
  └── Full-width forms
  └── Hamburger menu (if needed)

Tablet (768px - 1024px)
  └── Two-column grid for stats
  └── Sidebar hidden/collapsed

Desktop (> 1024px)
  └── Full sidebar visible
  └── Multi-column layouts
  └── Grid layouts for stats/cards
```

## Error Messages

| Error | Page | Message |
|-------|------|---------|
| Invalid email | Register/Login | "Invalid email address" |
| Weak password | Register/Settings | "Password must contain uppercase, lowercase, and number" |
| Username taken | Register | "Username already exists" |
| Email taken | Register | "Email already registered" |
| Invalid token | Verify/Reset | "Invalid or expired link" |
| Wrong password | Login | "Invalid email or password" |
| User not found | Reset | "No account found with this email" |

This flow ensures a secure, intuitive, and complete authentication and user management system for the LPanda community platform.
