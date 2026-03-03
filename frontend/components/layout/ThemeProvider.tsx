"use client";

import { useEffect } from "react";
import { useThemeStore } from "@/stores/themeStore";

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    const html = document.documentElement;
    if (theme === "light") {
      html.classList.add("light");
    } else {
      html.classList.remove("light");
    }
  }, [theme]);

  return <>{children}</>;
}
