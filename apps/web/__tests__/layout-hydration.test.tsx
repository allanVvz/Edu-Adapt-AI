import React from "react";
import { act } from "react-dom/test-utils";
import { hydrateRoot } from "react-dom/client";
import { renderToString } from "react-dom/server";
import StudentLayout from "@/components/layout/StudentLayout";

const cookieStore: Record<string, string> = {};

jest.mock("js-cookie", () => ({
  get: (key: string) => cookieStore[key] ?? undefined,
  set: (key: string, value: string) => { cookieStore[key] = value; },
  remove: (key: string) => { delete cookieStore[key]; },
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/student",
}));

describe("layout hydration", () => {
  beforeEach(() => {
    Object.keys(cookieStore).forEach((key) => delete cookieStore[key]);
  });

  it("hydrates StudentLayout without mismatching UserDropdown when user cookie exists", async () => {
    cookieStore.user = JSON.stringify({
      id: "student-1",
      name: "Aluno Teste",
      email: "aluno@test.local",
      role: "student",
    });

    const tree = (
      <StudentLayout>
        <p>Conteudo da atividade</p>
      </StudentLayout>
    );
    const serverHtml = renderToString(tree);
    expect(serverHtml).not.toContain("Aluno Teste");

    const container = document.createElement("div");
    container.innerHTML = serverHtml;
    document.body.appendChild(container);

    const consoleError = jest.spyOn(console, "error").mockImplementation(() => {});

    await act(async () => {
      hydrateRoot(container, tree);
      await Promise.resolve();
    });

    expect(consoleError.mock.calls.flat().join("\n")).not.toMatch(/Hydration failed|initial UI does not match/i);
    expect(container).toHaveTextContent("Aluno Teste");

    consoleError.mockRestore();
    container.remove();
  });
});
