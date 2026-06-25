"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { getCurrentUser } from "@/features/auth";

export default function HomePage() {
  const router = useRouter();
  const { isSuccess, isError } = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
    retry: false,
  });

  if (isSuccess) {
    router.replace("/projects");
    return null;
  }

  if (isError) {
    router.replace("/login");
    return null;
  }

  return (
    <main className="grid min-h-screen place-items-center text-sm text-[var(--text-muted)]">
      正在验证身份…
    </main>
  );
}
