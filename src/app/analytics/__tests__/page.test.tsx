import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAnalyticsOverview } from "@/lib/analytics";
import AnalyticsPage from "../page";

// Mock the auth context
jest.mock("@/contexts/AuthContext", () => ({
  useAuth: jest.fn(),
}));

// Mock the analytics lib
jest.mock("@/lib/analytics", () => ({
  fetchAnalyticsOverview: jest.fn(),
}));



// Mock theme hook
jest.mock("@/hooks/useTheme", () => ({
  useTheme: () => ({
    theme: "light",
    toggleTheme: jest.fn(),
    mounted: true,
  }),
}));

// Mock recharts
jest.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}));

const mockAuth = {
  getToken: jest.fn().mockReturnValue("test-token"),
  isAuthenticated: true,
  user: { id: "1", email: "test@example.com" },
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
};

const mockAnalyticsData = {
  total_posts: 42,
  published_posts: 38,
  avg_engagement_rate: 4.5,
  total_followers: 12500,
  follower_growth: [
    { date: "2024-01-01", followers: 12000 },
    { date: "2024-01-15", followers: 12200 },
    { date: "2024-01-30", followers: 12500 },
  ],
  platform_metrics: [
    { platform: "Twitter", followers: 5000, engagement_rate: 5.2, posts: 20 },
    { platform: "LinkedIn", followers: 3000, engagement_rate: 3.8, posts: 15 },
  ],
  recent_posts: [
    {
      id: "1",
      content: "Test post content",
      platform: "Twitter",
      status: "published",
      scheduled_at: null,
      published_at: "2024-01-30T12:00:00Z",
      likes: 150,
      replies: 25,
      reposts: 30,
      engagement_rate: 4.2,
    },
  ],
};

describe("Analytics Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue(mockAuth);
  });

  it("calls GET /api/analytics/overview on load", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(fetchAnalyticsOverview).toHaveBeenCalledWith("test-token", 30);
    });
  });

  it("renders metrics cards with actual numbers from API", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("4.50%")).toBeInTheDocument();
      expect(screen.getByText("12.5K")).toBeInTheDocument();
      expect(screen.getByText("38")).toBeInTheDocument();
    });
  });

  it("renders charts with real data from API", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
      expect(screen.getByText("Follower Growth (30 Days)")).toBeInTheDocument();
    });
  });

  it("updates API query params when time range filter changes", async () => {
    (fetchAnalyticsOverview as jest.Mock)
      .mockResolvedValueOnce(mockAnalyticsData)
      .mockResolvedValueOnce({ ...mockAnalyticsData, total_posts: 100 });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(fetchAnalyticsOverview).toHaveBeenCalledWith("test-token", 30);
    });

    const sevenDaysButton = screen.getByText("7 Days");
    fireEvent.click(sevenDaysButton);

    await waitFor(() => {
      expect(fetchAnalyticsOverview).toHaveBeenCalledWith("test-token", 7);
    });
  });

  it("shows loading skeleton during data fetch", () => {
    (fetchAnalyticsOverview as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<AnalyticsPage />);

    expect(screen.getByText("Loading analytics...")).toBeInTheDocument();
  });

  it("shows error state with retry button on API failure", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockRejectedValueOnce({
      message: "Network error",
      code: "NETWORK_ERROR",
    });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
      expect(screen.getByText("Try Again")).toBeInTheDocument();
    });
  });

  it("retries data fetch when retry button is clicked", async () => {
    (fetchAnalyticsOverview as jest.Mock)
      .mockRejectedValueOnce({
        message: "Network error",
        code: "NETWORK_ERROR",
      })
      .mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Try Again")).toBeInTheDocument();
    });

    const retryButton = screen.getByText("Try Again");
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(fetchAnalyticsOverview).toHaveBeenCalledTimes(2);
    });
  });

  it("shows empty state when no analytics data exists", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce({
      ...mockAnalyticsData,
      recent_posts: [],
      platform_metrics: [],
    });

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("No posts yet. Start creating content to see analytics.")).toBeInTheDocument();
      expect(screen.getByText("No platforms connected yet.")).toBeInTheDocument();
    });
  });

  it("displays platform metrics correctly", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      // Check Platform Performance section
      expect(screen.getByText("Platform Performance")).toBeInTheDocument();
      // Use getAllByText since "Twitter" appears in both platform metrics and recent posts
      const twitterElements = screen.getAllByText("Twitter");
      expect(twitterElements.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("LinkedIn")).toBeInTheDocument();
      expect(screen.getByText((content) => content.includes("5.20"))).toBeInTheDocument();
      expect(screen.getByText((content) => content.includes("3.80"))).toBeInTheDocument();
    });
  });

  it("displays recent posts correctly", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValueOnce(mockAnalyticsData);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText("Test post content")).toBeInTheDocument();
      expect(screen.getByText("published")).toBeInTheDocument();
      expect(screen.getByText("150")).toBeInTheDocument();
    });
  });

  it("allows selecting different time ranges", async () => {
    (fetchAnalyticsOverview as jest.Mock).mockResolvedValue(mockAnalyticsData);

    render(<AnalyticsPage />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    const ninetyDaysButton = screen.getByText("90 Days");
    fireEvent.click(ninetyDaysButton);

    await waitFor(() => {
      expect(fetchAnalyticsOverview).toHaveBeenCalledWith("test-token", 90);
    });
  });
});
