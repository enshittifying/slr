# Stanford Law Review - Frontend

Next.js 14 frontend for the Stanford Law Review Citation System.

## Features

- ✅ Next.js 14 with App Router
- ✅ TypeScript for type safety
- ✅ Tailwind CSS for styling
- ✅ NextAuth.js for Google OAuth authentication
- ✅ React Query for data fetching
- ✅ Responsive design
- ✅ Dashboard with user and article management

## Getting Started

### Development

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your credentials

# Run development server
npm run dev
```

Visit http://localhost:3000

### Build for Production

```bash
npm run build
npm start
```

## Environment Variables

Required environment variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_secret_here
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## Deployment

Deploy to Vercel:

```bash
npm i -g vercel
vercel
```

Or push to GitHub and connect to Vercel dashboard.

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/          # Login page
│   ├── dashboard/          # Protected dashboard routes
│   │   ├── users/          # User management
│   │   └── articles/       # Article management
│   ├── api/auth/           # NextAuth API routes
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── providers.tsx       # React Query & NextAuth providers
├── lib/
│   └── api-client.ts       # API client with axios
├── components/             # Reusable components
└── types/                  # TypeScript types
```

## Features

- **Authentication**: Google OAuth with stanford.edu domain restriction
- **Dashboard**: Overview of system statistics
- **User Management**: View and manage users with roles
- **Article Management**: Track articles through the validation pipeline
- **Real-time Data**: React Query for efficient data fetching and caching

## Tech Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- NextAuth.js
- React Query
- Axios
- Lucide Icons
