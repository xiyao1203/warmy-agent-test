"use client";

import type {
  CreateModelConfigRequest,
  ModelPurpose,
  UpdateModelConfigRequest,
} from "@warmy/generated-api-client";
import { useCallback, useEffect, useState } from "react";

import { problemMessage } from "@/lib/api/problem";

import {
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
  const [models, setModels] = useState<
    Awaited<ReturnType<typeof listModelConfigs>>
  >([]);
  const [defaults, setDefaults] = useState<
    Awaited<ReturnType<typeof listModelDefaults>>
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    try {
      const [nextModels, nextDefaults] = await Promise.all([
        listModelConfigs(projectId),
        listModelDefaults(projectId),
      ]);
      setModels(nextModels);
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
  }, [projectId]);

  useEffect(() => {
    let active = true;
    void Promise.all([listModelConfigs(projectId), listModelDefaults(projectId)])
      .then(([nextModels, nextDefaults]) => {
        if (!active) return;
        setModels(nextModels);
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
  }, [projectId]);

  return (
    <ModelConfigList
      defaults={defaults}
      error={error || undefined}
      loading={loading}
      models={models}
      onCreate={async (value: CreateModelConfigRequest) => {
        await createModelConfig(projectId, value);
        await reload();
      }}
      onDelete={async (id) => {
        await deleteModelConfig(projectId, id);
        await reload();
      }}
      onSetDefault={async (purpose: ModelPurpose, id) => {
        if (!id) return;
        await setModelDefault(projectId, purpose, id);
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
