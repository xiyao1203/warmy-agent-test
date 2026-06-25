"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth";
import { problemKind } from "@/lib/api/problem";

import { createUser, listUsers, resetUserPassword, setUserEnabled } from "./api";
import { UserManagement } from "./user-management";

export function UserManagementScreen() {
  const userQuery = useQuery({ queryFn: getCurrentUser, queryKey: ["session"] });
  const usersQuery = useQuery({
    enabled: userQuery.data?.role === "super_admin",
    queryFn: () => listUsers(),
    queryKey: ["users"],
  });
  const placeholderUser = {
    display_name: "",
    email: "",
    id: "",
    must_change_password: false,
    role: "viewer" as const,
    status: "active" as const,
  };

  if (userQuery.isPending) {
    return <UserManagement currentUser={placeholderUser} loading />;
  }
  if (userQuery.isError || userQuery.data.role !== "super_admin") {
    return (
      <UserManagement currentUser={userQuery.data ?? placeholderUser} error="permission" />
    );
  }
  if (usersQuery.isPending) {
    return <UserManagement currentUser={userQuery.data} loading />;
  }
  if (usersQuery.isError) {
    return (
      <UserManagement
        currentUser={userQuery.data}
        error={problemKind(usersQuery.error) === "permission" ? "permission" : "service"}
      />
    );
  }
  return (
    <UserManagement
      currentUser={userQuery.data}
      nextCursor={usersQuery.data.next_cursor}
      onCreate={async (payload) => {
        await createUser(payload);
        await usersQuery.refetch();
      }}
      onResetPassword={async (userId, password) => {
        await resetUserPassword(userId, password);
        await usersQuery.refetch();
      }}
      onToggleStatus={async (userId, enabled) => {
        await setUserEnabled(userId, enabled);
        await usersQuery.refetch();
      }}
      users={usersQuery.data.items}
    />
  );
}
