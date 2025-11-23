#!/bin/bash

echo "🚀 Deploying Stanford Law Review Frontend to Vercel..."
echo ""

# Check if vercel is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm i -g vercel
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the frontend directory"
    exit 1
fi

echo "✅ Vercel CLI found"
echo ""

# Check if environment file exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  No .env.local file found. Copying from example..."
    cp .env.local.example .env.local
    echo "📝 Please edit .env.local with your credentials before deploying to production"
    echo ""
fi

echo "📦 Installing dependencies..."
npm install

echo ""
echo "🏗️  Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix errors and try again."
    exit 1
fi

echo "✅ Build successful!"
echo ""

read -p "Deploy to Vercel now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Deploying to Vercel..."
    echo ""
    echo "Important: Make sure to set these environment variables in Vercel:"
    echo "  - NEXT_PUBLIC_API_URL (your backend API URL)"
    echo "  - NEXTAUTH_URL (https://slro.vercel.app)"
    echo "  - NEXTAUTH_SECRET (generate with: openssl rand -base64 32)"
    echo "  - GOOGLE_CLIENT_ID"
    echo "  - GOOGLE_CLIENT_SECRET"
    echo ""

    vercel --prod

    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Visit https://vercel.com/dashboard and add environment variables"
    echo "2. Redeploy after adding variables: vercel --prod"
    echo "3. Update Google OAuth redirect URIs to include your Vercel URL"
    echo "4. Test the deployment at https://slro.vercel.app"
else
    echo ""
    echo "ℹ️  Deployment cancelled. To deploy later, run:"
    echo "   vercel --prod"
fi

echo ""
echo "📖 For detailed deployment instructions, see ../DEPLOYMENT.md"
