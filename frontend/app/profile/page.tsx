"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { getMBTIColor } from "@/lib/utils";
import type { MBTIType } from "@/types";

const MBTI_TYPES: MBTIType[] = [
  "INTJ", "INTP", "ENTJ", "ENTP",
  "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
  "ISTP", "ISFP", "ESTP", "ESFP",
];

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, fetchUser, updateMBTI, logout } = useAuthStore();
  const [selectedMBTI, setSelectedMBTI] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }
    fetchUser();
  }, [isAuthenticated, router, fetchUser]);

  useEffect(() => {
    if (user?.mbti) {
      setSelectedMBTI(user.mbti);
    }
  }, [user]);

  const handleMBTIChange = async (mbti: string) => {
    setSelectedMBTI(mbti);
    setSaving(true);
    try {
      await updateMBTI(mbti);
    } catch (error) {
      console.error("Failed to update MBTI:", error);
    } finally {
      setSaving(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4 bg-dark-200">
      <div className="max-w-2xl mx-auto">
        {/* Profile Header */}
        <div className="bg-dark-100 rounded-lg p-8 mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 rounded-full bg-primary-600 flex items-center justify-center">
              <span className="text-3xl font-bold text-white">
                {user.nickname.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{user.nickname}</h1>
              <p className="text-white/60">{user.email}</p>
              {user.mbti && (
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-sm text-white ${getMBTIColor(user.mbti)}`}>
                  {user.mbti}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* MBTI Selection */}
        <div className="bg-dark-100 rounded-lg p-8 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">MBTI 설정</h2>
          <p className="text-white/60 mb-6">
            MBTI를 설정하면 성격에 맞는 영화를 추천받을 수 있어요.
          </p>

          <div className="grid grid-cols-4 gap-3">
            {MBTI_TYPES.map((mbti) => (
              <button
                key={mbti}
                onClick={() => handleMBTIChange(mbti)}
                disabled={saving}
                className={`py-3 rounded-lg font-medium transition ${
                  selectedMBTI === mbti
                    ? `${getMBTIColor(mbti)} text-white`
                    : "bg-dark-200 text-white/60 hover:bg-dark-200/70"
                }`}
              >
                {mbti}
              </button>
            ))}
          </div>

          {saving && (
            <p className="text-primary-500 text-sm mt-4">저장 중...</p>
          )}
        </div>

        {/* Account Actions */}
        <div className="bg-dark-100 rounded-lg p-8">
          <h2 className="text-xl font-bold text-white mb-4">계정</h2>
          <button
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="px-6 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-md transition"
          >
            로그아웃
          </button>
        </div>
      </div>
    </div>
  );
}
