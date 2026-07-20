"use client";

import type {
  CreateModelConfigRequest,
  ModelConfigResponse,
  ModelPurpose,
  UpdateModelConfigRequest,
} from "@warmy/generated-api-client";
import { useCallback, useEffect, useState } from "react";

import { problemMessage } from "@/lib/api/problem";
import { normalizeResourcePage } from "@/lib/pagination";
import { usePaginationState } from "@/lib/use-pagination-state";

import {
  clearModelDefault,
  createModelConfig,
  deleteModelConfig,
  listModelConfigs,
  listModelDefaults,
  setModelDefault,
  testModelConnection,
  updateModelConfig,
} from "./api";
import { ModelConfigList } from "./model-config-list";

export function ModelConfigScreen({ projectId }: { projectId: string }) {
  const pagination = usePaginationState();
  const [models, setModels] = useState<ModelConfigResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [defaults, setDefaults] = useState<
    Awaited<ReturnType<typeof listModelDefaults>>
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    try {
      const [nextModels, nextDefaults] = await Promise.all([
        listModelConfigs(projectId, pagination.page, pagination.pageSize),
        listModelDefaults(projectId),
      ]);
      const page = normalizeResourcePage(
        nextModels,
        pagination.page,
        pagination.pageSize,
      );
      setModels(page.items);
      setTotal(page.total);
      setTotalPages(page.total_pages);
      setDefaults(nextDefaults);
      setError("");
    } catch (error) {
      setError(
        problemMessage(
          error,
          "请刷新重试；若持续失败，请检查项目权限或 Control API。",
        ),
      );
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, projectId]);

  useEffect(() => {
    let active = true;
    void Promise.all([
      listModelConfigs(projectId, pagination.page, pagination.pageSize),
      listModelDefaults(projectId),
    ])
      .then(([nextModels, nextDefaults]) => {
        if (!active) return;
        const page = normalizeResourcePage(
          nextModels,
          pagination.page,
          pagination.pageSize,
        );
        setModels(page.items);
        setTotal(page.total);
        setTotalPages(page.total_pages);
        setDefaults(nextDefaults);
        setError("");
      })
      .catch((error: unknown) => {
        if (!active) return;
        setError(
          problemMessage(
            error,
            "请刷新重试；若持续失败，请检查项目权限或 Control API。",
          ),
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pagination.page, pagination.pageSize, projectId]);

  return (
    <ModelConfigList
      defaults={defaults}
      error={error || undefined}
      loading={loading}
      models={models}
      onPageChange={pagination.setPage}
      onPageSizeChange={pagination.setPageSize}
      page={pagination.page}
      pageSize={pagination.pageSize}
      total={total}
      totalPages={totalPages}
      onCreate={async (value: CreateModelConfigRequest) => {
        await createModelConfig(projectId, value);
        await reload();
      }}
      onDelete={async (id) => {
        await deleteModelConfig(projectId, id);
        await reload();
      }}
      onSetDefault={async (purpose: ModelPurpose, id) => {
        if (!id) {
          await clearModelDefault(projectId, purpose);
        } else {
          await setModelDefault(projectId, purpose, id);
        }
        await reload();
      }}
      onTestConnection={(id) => testModelConnection(projectId, id)}
      onUpdate={async (id, value: UpdateModelConfigRequest) => {
        await updateModelConfig(projectId, id, value);
        await reload();
      }}
    />
  );
}
