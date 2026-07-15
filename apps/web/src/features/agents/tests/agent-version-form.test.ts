import { describe, expect, it } from "vitest";

import { buildAgentVersionPayload } from "../agent-version-form";

describe("buildAgentVersionPayload", () => {
  it("references the saved credential without carrying plaintext login fields", () => {
    const payload = buildAgentVersionPayload({
      adapterId: "",
      adapterVersion: "",
      apiUrl: "https://agent.example.test/api",
      blockedActions: ["delete"],
      browserProfileId: "",
      codeVersion: "",
      costLimit: "",
      credential: {
        bindingId: "credential-1",
        password: "secret-password",
        username: "user@example.test",
      },
      credentialBindingIds: ["credential-2"],
      entryUrl: "https://agent.example.test",
      gitCommit: "",
      knowledgeVersion: "",
      loginStrategy: "credential",
      maxSteps: "20",
      model: "",
      modelParams: {},
      plugin: {
        description: "test",
        pluginId: "generic-web-agent",
        targetType: "web_agent",
        version: "1.0.0",
      },
      promptInputSelector: "textarea",
      protocol: "sync_json",
      requestTemplate: { input: "{{ input }}" },
      requiresConfirmation: true,
      responsePath: "output",
      responseSelector: "",
      sendButtonSelector: "button[type='submit']",
      systemPrompt: "",
      systemPromptVersion: "",
      testScope: "readonly",
      timeout: 30,
      tools: [],
    });

    expect(payload.config.credential_binding_ids).toEqual([
      "credential-2",
      "credential-1",
    ]);
    expect(payload.config.target_config).toMatchObject({
      login: {
        credential_binding_id: "credential-1",
        strategy: "credential",
      },
    });
    expect(JSON.stringify(payload)).not.toContain("secret-password");
    expect(JSON.stringify(payload)).not.toContain("user@example.test");
  });
});
