# LPanda Platform - Frontend

Modern, responsive frontend for the LPanda Meta-Jungle Task & Reward Management Platform.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: React Query
- **Forms**: React Hook Form + Zod
- **Icons**: Lucide React
- **Charts**: Recharts
- **Notifications**: Sonner

## Features

- 🔐 **Authentication**: JWT-based auth with automatic token refresh
- 👥 **Role-Based Access**: Support for 4 user roles (Overall_Admin, Ambassador_Admin, Team_Member, Ambassador)
- 📋 **Task Management**: Create, assign, and track tasks
- 📤 **Submissions**: Submit tasks with text, links, and file uploads
- 🏆 **Leaderboard**: Separate leaderboards for Team Members and Ambassadors
- 💰 **Points System**: Track Panda Points (PP) and transaction history
- 📅 **Schedule**: View and manage calendar events
- 📢 **Announcements**: Targeted messaging system
- 📊 **Dashboard**: Personalized dashboard with analytics
- 🌙 **Dark Mode**: Full dark mode support
- 📱 **Responsive**: Mobile-first design

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app router pages
│   │   ├── (auth)/         # Authentication pages
│   │   ├── (dashboard)/    # Dashboard pages
│   │   ├── layout.tsx      # Root layout
│   │   └── page.tsx        # Home page
│   ├── components/         # React components
│   │   ├── ui/            # Reusable UI components
│   │   ├── layout/        # Layout components
│   │   └── features/      # Feature-specific components
│   ├── lib/               # Utility functions
│   │   ├── api.ts         # API client
│   │   ├── auth.ts        # Auth utilities
│   │   └── utils.ts       # General utilities
│   ├── hooks/             # Custom React hooks
│   ├── store/             # Zustand stores
│   ├── types/             # TypeScript types
│   └── api/               # API service functions
├── public/                # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking
- `npm run format` - Format code with Prettier

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `LPanda Platform` |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | Enable analytics | `false` |
| `NEXT_PUBLIC_ENABLE_WEBSOCKET` | Enable WebSocket | `false` |

## User Roles

### Overall_Admin
- Full system access
- Manage all users, tasks, schedules, and announcements
- View all submissions and leaderboards
- Award/penalize points

### Ambassador_Admin
- Manage Ambassadors only
- Create tasks for Ambassadors
- View Ambassador leaderboard
- Limited administrative access

### Team_Member
- Complete assigned tasks
- Submit task completions
- View Team Member leaderboard
- Track personal points

### Ambassador
- Complete assigned tasks
- Submit task completions
- View Ambassador leaderboard
- Track personal points

## Key Features

### Authentication
- Login with email and password
- JWT token-based authentication
- Automatic token refresh
- Secure session management

### Dashboard
- Personalized based on user role
- Quick stats (tasks, points, rank)
- Recent activity feed
- Upcoming deadlines

### Task Management
- Create and assign tasks (Admin)
- View assigned tasks
- Submit task completions
- Track submission status

### Points System
- Earn points for task completion
  - Team Members: 50 PP per task
  - Ambassadors: 138.6 PP per task
- Deadline penalties: -100 PP
- Admin bonuses and penalties
- Complete transaction history

### Leaderboard
- Separate rankings for Team Members and Ambassadors
- Real-time rank updates
- Points breakdown
- Historical trends

## API Integration

The frontend communicates with the backend API using:
- **Axios**: HTTP client
- **React Query**: Data fetching and caching
- **Automatic retries**: Failed requests retry automatically
- **Error handling**: Standardized error responses

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom theme**: Brand colors and typography
- **Responsive design**: Mobile-first approach
- **Dark mode**: Full dark mode support

## State Management

- **Zustand**: Lightweight state management
- **React Query**: Server state management
- **Local storage**: Persistent client state

## Form Handling

- **React Hook Form**: Performant form library
- **Zod**: Schema validation
- **Type-safe**: Full TypeScript support

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

Proprietary - LPanda Platform

## Support

For issues or questions, contact the development team.
