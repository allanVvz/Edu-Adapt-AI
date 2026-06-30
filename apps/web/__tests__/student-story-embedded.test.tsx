import React from "react";
import { render, screen } from "@testing-library/react";
import StudentActivityPage from "../app/(student)/student/activities/[id]/page";
import api from "@/lib/api";

jest.mock("@/components/layout/StudentLayout", () => ({
  __esModule: true,
  default: ({ children, headerAction }: { children: React.ReactNode; headerAction?: React.ReactNode }) => (
    <main>
      {headerAction}
      {children}
    </main>
  ),
}));

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "adaptation-1" }),
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe("Student embedded story", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.get.mockResolvedValue({
      data: {
        title: "Sequência de acontecimentos: O Coelho e a Chuva",
        story: {
          id: "story-ravi-nina",
          title: "O Coelho e a Chuva",
          content: "Ravi encontrou Nina durante a chuva.",
          image_options: [
            { id: "story_img_1", description: "Ravi", emoji: "🐰", is_active: true },
            { id: "story_img_2", description: "Nina", emoji: "🐢", is_active: true },
          ],
          audio_options: [
            { id: "story_audio_1", script: "Ravi encontrou Nina.", audio_url: null },
          ],
        },
        output: {
          text_adaptations: [{ version: 1, content: "Agora responda a atividade." }],
          image_options: [],
          audio_options: [],
          interaction_options: [
            {
              type: "multiple_choice",
              instructions: "O que aconteceu primeiro?",
              items: [{ name: "Minha resposta" }],
              zones: [{ name: "Ravi acordou" }, { name: "Encontrou Nina" }],
              correct_answer: { correct_zone: "Ravi acordou" },
            },
          ],
        },
      },
    });
    mockedApi.post.mockResolvedValue({ data: {} });
  });

  it("renders the story inline before the activity content", async () => {
    render(<StudentActivityPage />);

    const storyTitle = await screen.findByText("O Coelho e a Chuva");
    const activityText = await screen.findByText("Agora responda a atividade.");

    expect(storyTitle).toBeInTheDocument();
    expect(screen.getByText("Ravi encontrou Nina durante a chuva.")).toBeInTheDocument();
    expect(screen.getByText("Ravi")).toBeInTheDocument();
    expect(screen.getByText("Nina")).toBeInTheDocument();
    expect(screen.getByText("Narração do conto")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ouvir narração" })).toBeInTheDocument();

    const position = storyTitle.compareDocumentPosition(activityText);
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
