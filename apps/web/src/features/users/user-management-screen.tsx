"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import type { UserResponse } from "@warmy/generated-api-client";

import { getCurrentUser } from "@/features/auth";
import { problemKind } from "@/lib/api/problem";

import {
  createUser,
  deleteUser,
  listUsers,
  resetUserPassword,
  setUserEnabled,
  updateUser,
} from "./api";
import { UserManagement } from "./user-management";

type LoadedUserPage = {
  baseUpdatedAt: number;
  items: UserResponse[];
  nextCursor: string | null;
} | null;

export function UserManagementScreen() {
  const [loadedPage, setLoadedPage] = useState<LoadedUserPage>(null);
  const [paging, setPaging] = useState(false);
  const userQuery = useQuery({
    queryFn: getCurrentUser,
    queryKey: ["session"],
  });
  const usersQuery = useQuery({
    enabled: userQuery.data?.role === "super_admin",
    queryFn: () => listUsers(),
    queryKey: ["users"],
  });
  const baseUsers = usersQuery.data?.items ?? [];
  const loadedPageMatchesCurrentQuery =
    loadedPage?.baseUpdatedAt === usersQuery.dataUpdatedAt;
  const users = loadedPageMatchesCurrentQuery
    ? [...baseUsers, ...loadedPage.items]
    : baseUsers;
  const nextCursor = loadedPageMatchesCurrentQuery
    ? loadedPage.nextCursor
    : (usersQuery.data?.next_cursor ?? null);

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
      nextCursor={nextCursor}
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
      onLoadMore={async () => {
        if (!nextCursor || paging) return;
        setPaging(true);
        try {
          const page = await listUsers(nextCursor);
          setLoadedPage((current) => {
            const currentItems =
              current?.baseUpdatedAt === usersQuery.dataUpdatedAt
                ? current.items
                : [];
            return {
              baseUpdatedAt: usersQuery.dataUpdatedAt,
              items: [...currentItems, ...page.items],
              nextCursor: page.next_cursor,
            };
          });
        } finally {
          setPaging(false);
        }
      }}
      onResetPassword={async (userId, password) => {
        await resetUserPassword(userId, password);
        await usersQuery.refetch();
      }}
      onToggleStatus={async (userId, enabled) => {
        await setUserEnabled(userId, enabled);
        await usersQuery.refetch();
      }}
      paging={paging}
      users={users}
    />
  );
}
