import type { UserResponse } from "@warmy/generated-api-client";

export function canManageUsers(user: Pick<UserResponse, "role">) {
  return user.role === "super_admin";
}
