"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import * as api from "@/lib/api";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { socialLogin } = useAuthStore();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error || !code) {
      router.replace("/login?error=google_failed");
      return;
    }

    api
      .googleLogin(code)
      .then((response) => {
        const isNew = socialLogin(response);
        router.replace(isNew ? "/onboarding" : "/");
      })
      .catch(() => {
        router.replace("/login?error=google_failed");
      });
  }, [searchParams, socialLogin, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-200">
      <div className="text-center">
        <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white/60">Google 로그인 처리 중...</p>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-dark-200">
          <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
