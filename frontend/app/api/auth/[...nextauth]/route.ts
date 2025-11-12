import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          hd: 'stanford.edu', // Restrict to Stanford domain
          prompt: 'select_account',
        },
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // Verify stanford.edu domain
      const email = user.email || ''
      if (process.env.NODE_ENV === 'production' && !email.endsWith('@stanford.edu')) {
        return false
      }
      return true
    },
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.id_token
      }
      return token
    },
    async session({ session, token }) {
      if (session) {
        session.accessToken = token.accessToken as string
      }
      return session
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
})

export { handler as GET, handler as POST }
