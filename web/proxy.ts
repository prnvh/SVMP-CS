import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse, type NextRequest } from "next/server";
import { isClerkConfigured } from "@/lib/clerk-env";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/sessions(.*)",
  "/knowledge-base(.*)",
  "/brand-voice(.*)",
  "/governance(.*)",
  "/metrics(.*)",
  "/integrations(.*)",
  "/settings(.*)",
  "/onboarding(.*)",
]);

const authProxy = clerkMiddleware(async (auth, request) => {
  if (isProtectedRoute(request)) {
    await auth.protect();
  }
});

const passthroughProxy = (request: NextRequest) => NextResponse.next({ request });

export default isClerkConfigured() ? authProxy : passthroughProxy;

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
