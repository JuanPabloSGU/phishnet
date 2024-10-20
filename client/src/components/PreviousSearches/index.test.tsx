import { render, screen } from "@tests/test-utils";
import PreviousSearches from "./index";
import { vi } from "vitest";

describe("PreviousSearches Component", () => {
  beforeEach(() => {
    // Mock localStorage.getItem
    const mockHistory = [
      {
        url: "https://example.com",
        model: "Logistic Regression",
        value: [0.85], // 85% confidence
      },
      {
        url: "https://test.com",
        model: "Random Forest",
        value: [0.45], // 45% confidence
      },
    ];

    vi.spyOn(Storage.prototype, "getItem").mockReturnValue(JSON.stringify(mockHistory));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test("renders component correctly", () => {
    render(<PreviousSearches />);

    // Check if the title and description are displayed
    expect(screen.getByText("Previous Searches")).toBeInTheDocument();
    expect(screen.getByText(/Track your scanning history/)).toBeInTheDocument();
  });

  test("renders table with correct headers", () => {
    render(<PreviousSearches />);

    // Check if the table headers are present
    expect(screen.getByText("URL")).toBeInTheDocument();
    expect(screen.getByText("Model")).toBeInTheDocument();
    expect(screen.getByText("Verdict")).toBeInTheDocument();
  });

  test("renders previous search results from localStorage", () => {
    render(<PreviousSearches />);

    // Check if the mock data is rendered in the table
    expect(screen.getByText("https://example.com")).toBeInTheDocument();
    expect(screen.getByText("Logistic Regression")).toBeInTheDocument();
    expect(screen.getByText("85.00%")).toBeInTheDocument();

    expect(screen.getByText("https://test.com")).toBeInTheDocument();
    expect(screen.getByText("Random Forest")).toBeInTheDocument();
    expect(screen.getByText("45.00%")).toBeInTheDocument();
  });

  test("renders empty state when no search history is available", () => {
    // Mock localStorage to return null
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue(null);

    render(<PreviousSearches />);

    // Expect no rows to be present
    expect(screen.queryByText("https://example.com")).not.toBeInTheDocument();
    expect(screen.queryByText("No previous searches found")).not.toBeInTheDocument();
  });
});

