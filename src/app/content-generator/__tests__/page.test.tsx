import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ContentGeneratorPage from "../page";
import { AuthProvider } from "@/contexts/AuthContext";

// Mock the AuthContext
jest.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    getToken: () => "mock-token",
    isAuthenticated: true,
    user: { id: "user-1", email: "test@example.com", name: "Test User" },
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

// Mock the DashboardLayout and ProtectedRoute
jest.mock("@/components/layout/DashboardLayout", () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  ),
}));

jest.mock("@/components/auth/ProtectedRoute", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

describe("ContentGeneratorPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
    (localStorage.setItem as jest.Mock).mockClear();
    (localStorage.getItem as jest.Mock).mockReturnValue(null);
  });

  it("renders the content generator page", () => {
    render(<ContentGeneratorPage />);
    
    expect(screen.getByText("Content Generator")).toBeInTheDocument();
    expect(screen.getByText("Create engaging content with AI assistance.")).toBeInTheDocument();
  });

  it("displays content type options", () => {
    render(<ContentGeneratorPage />);
    
    expect(screen.getByText("Post")).toBeInTheDocument();
    expect(screen.getByText("Thread")).toBeInTheDocument();
    expect(screen.getByText("Hashtags")).toBeInTheDocument();
    expect(screen.getByText("Images")).toBeInTheDocument();
  });

  it("displays platform selection buttons", () => {
    render(<ContentGeneratorPage />);
    
    expect(screen.getByText("Twitter/X")).toBeInTheDocument();
    expect(screen.getByText("LinkedIn")).toBeInTheDocument();
    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("Bluesky")).toBeInTheDocument();
  });

  it("shows empty state when no content generated", () => {
    render(<ContentGeneratorPage />);
    
    expect(screen.getByText("Ready to Create")).toBeInTheDocument();
    expect(screen.getByText("Enter a topic above and click Generate to create AI-powered content.")).toBeInTheDocument();
  });

  it("shows error when submitting without topic", async () => {
    render(<ContentGeneratorPage />);
    
    // Find and submit the form directly to bypass disabled button
    const form = screen.getByPlaceholderText("Describe what you want to write about...").closest("form");
    fireEvent.submit(form!);
    
    await waitFor(() => {
      expect(screen.getByText("Please enter a topic or prompt")).toBeInTheDocument();
    });
  });

  it("submits form with correct data", async () => {
    const mockResponse = {
      content: "Generated post content",
      provider: { provider: "minimax", model: "MiniMax-Text-01" },
      char_count: 100,
      estimated_read_time: "< 1 min",
    };
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<ContentGeneratorPage />);
    
    // Enter topic
    const topicInput = screen.getByPlaceholderText("Describe what you want to write about...");
    await userEvent.type(topicInput, "Test topic");
    
    // Submit form
    const generateButton = screen.getByRole("button", { name: /generate content/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/ai/generate",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            "Authorization": "Bearer mock-token",
          }),
          body: expect.stringContaining("Test topic"),
        })
      );
    });
  });

  it("displays loading state during API call", async () => {
    (fetch as jest.Mock).mockImplementationOnce(() => new Promise(() => {})); // Never resolves
    
    render(<ContentGeneratorPage />);
    
    // Enter topic and submit
    const topicInput = screen.getByPlaceholderText("Describe what you want to write about...");
    await userEvent.type(topicInput, "Test topic");
    
    const generateButton = screen.getByRole("button", { name: /generate content/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText("Generating...")).toBeInTheDocument();
    });
  });

  it("displays error state when API fails", async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: { message: "API Error" } }),
    });

    render(<ContentGeneratorPage />);
    
    const topicInput = screen.getByPlaceholderText("Describe what you want to write about...");
    await userEvent.type(topicInput, "Test topic");
    
    const generateButton = screen.getByRole("button", { name: /generate content/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText("API Error")).toBeInTheDocument();
    });
  });

  it("displays generated content on success", async () => {
    const mockResponse = {
      content: "This is the generated content",
      provider: { provider: "minimax", model: "MiniMax-Text-01" },
      char_count: 30,
      estimated_read_time: "< 1 min",
    };
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<ContentGeneratorPage />);
    
    const topicInput = screen.getByPlaceholderText("Describe what you want to write about...");
    await userEvent.type(topicInput, "Test topic");
    
    const generateButton = screen.getByRole("button", { name: /generate content/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText("Generated Content")).toBeInTheDocument();
      expect(screen.getByText("This is the generated content")).toBeInTheDocument();
      expect(screen.getByText("30 characters")).toBeInTheDocument();
    });
  });

  it("persists platform selection to localStorage", async () => {
    render(<ContentGeneratorPage />);
    
    const linkedinButton = screen.getByText("LinkedIn");
    fireEvent.click(linkedinButton);
    
    expect(localStorage.setItem).toHaveBeenCalledWith("smp_selected_platform", "linkedin");
  });

  it("allows selecting different tones", () => {
    render(<ContentGeneratorPage />);
    
    const wittyButton = screen.getByText("witty");
    fireEvent.click(wittyButton);
    
    expect(wittyButton).toHaveClass("bg-[var(--primary)]");
  });

  it("allows selecting different content types", () => {
    render(<ContentGeneratorPage />);
    
    const threadButton = screen.getByText("Thread").closest("button");
    fireEvent.click(threadButton!);
    
    expect(threadButton).toHaveClass("border-[var(--primary)]");
  });

  it("copies content to clipboard", async () => {
    const mockResponse = {
      content: "Content to copy",
      provider: { provider: "minimax", model: "MiniMax-Text-01" },
      char_count: 15,
      estimated_read_time: "< 1 min",
    };
    
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    render(<ContentGeneratorPage />);
    
    const topicInput = screen.getByPlaceholderText("Describe what you want to write about...");
    await userEvent.type(topicInput, "Test topic");
    
    const generateButton = screen.getByRole("button", { name: /generate content/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText("Content to copy")).toBeInTheDocument();
    });
    
    const copyButton = screen.getByText("Copy").closest("button");
    fireEvent.click(copyButton!);
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith("Content to copy");
  });
});
