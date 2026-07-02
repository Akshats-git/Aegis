import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";

const providers: NextAuthOptions["providers"] = [];

// Google sign-in (enabled when OAuth credentials are configured).
if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
  providers.push(
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
  );
}

// Guest sign-in so the app is usable before Google is configured.
providers.push(
  CredentialsProvider({
    id: "guest",
    name: "Guest",
    credentials: {},
    async authorize() {
      return { id: "guest@aegis.local", name: "Guest", email: "guest@aegis.local" };
    },
  }),
);

export const authOptions: NextAuthOptions = {
  providers,
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.uid = (user as { id?: string }).id ?? token.email ?? undefined;
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as { id?: string }).id =
          (token.uid as string) ?? token.email ?? "guest@aegis.local";
      }
      return session;
    },
  },
};

export const googleEnabled = Boolean(
  process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET,
);
