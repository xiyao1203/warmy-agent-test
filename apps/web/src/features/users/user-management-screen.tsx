"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth";
import { problemKind } from "@/lib/api/problem";
import { usePaginationState } from "@/lib/use-pagination-state";

import {
  createUser,
  deleteUser,
  listUsers,
  resetUserPassword,
  setUserEnabled,
  updateUser,
} from "./api";
import { UserManagement } from "./user-management";

export function UserManagementScreen() {
  const pagination = usePaginationState();
  const userQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
  });
  const usersQuery = useQuery({
    enabled: userQuery.data?.role === "super_admin",
    queryFn: () => listUsers(pagination.page, pagination.pageSize),
    queryKey: ["users", pagination.page, pagination.pageSize],
  });

  if (userQuery.isPending) {
    return <UserManagement loading />;
  }
  if (userQuery.isError || userQuery.data.role !== "super_admin") {
    return <UserManagement currentUser={userQuery.data} error="permission" />;
  }
  if (usersQuery.isPending) {
    return <UserManagement currentUser={userQuery.data} loading />;
  }
  if (usersQuery.isError) {
    return (
      <UserManagement
        currentUser={userQuery.data}
        error={
          problemKind(usersQuery.error) === "permission"
            ? "permission"
            : "service"
        }
      />
    );
  }
  return (
    <UserManagement
      currentUser={userQuery.data}
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      onCreate={async (payload) => {
        await createUser(payload);
        await usersQuery.refetch();
      }}
      onDelete={async (userId) => {
        await deleteUser(userId);
        await usersQuery.refetch();
      }}
      onEdit={async (userId, payload) => {
        await updateUser(userId, payload);
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
      page={usersQuery.data.page ?? pagination.page}
      pageSize={pagination.pageSize}
      total={usersQuery.data.total}
      totalPages={usersQuery.data.total_pages}
      users={usersQuery.data.items}
    />
  );
}
