"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getCurrentUser } from "@/features/auth";

export default function HomePage() {
  const router = useRouter();
  const { isSuccess, isError } = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
    retry: false,
  });

  useEffect(() => {
    if (isSuccess) router.replace("/projects");
    if (isError) router.replace("/login");
  }, [isError, isSuccess, router]);

  if (isSuccess || isError) {
    return null;
  }

  return (
    <main className="grid min-h-screen place-items-center text-sm text-[var(--muted)]">
      正在验证身份…
    </main>
  );
}
