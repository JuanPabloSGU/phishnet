import { fireEvent, render, screen, waitFor } from "@tests/test-utils";
import Inference from "./index";
import axios from "axios";
import InferenceResult from "@components/InferenceResult";

import { vi } from 'vitest';
// Mock axios and InferenceResult component
vi.mock("axios");

vi.mock("@components/InferenceResult", () => ({
  default: vi.fn(() => <div>Mock Inference Result</div>),
}));

describe("Inference Component", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  test("renders component correctly", () => {
    render(<Inference />);

    expect(screen.getByText("Scan")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Enter a URL below to instantly assess its authenticity/,
      ),
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter a URL, e.g. https://example.com"))
      .toBeInTheDocument();
    expect(screen.getByText("Submit")).toBeInTheDocument();
  });

  test("allows URL input", () => {
    render(<Inference />);
    const input = screen.getByPlaceholderText(
      "Enter a URL, e.g. https://example.com",
    );

    fireEvent.change(input, { target: { value: "https://example.com" } });
    expect(input).toHaveValue("https://example.com");
  });

  test("allows model selection", () => {
    render(<Inference />);
    const segmentedControl = screen.getByRole("radiogroup");

    fireEvent.click(screen.getByText("Random Forest"));
    expect(segmentedControl).toHaveTextContent("Random Forest");
  });

  test("handles successful inference", async () => {
    (axios as vi.Mocked<typeof axios>).mockResolvedValue({
      data: {
        triton: { outputs: [{ data: [0.7] }] },
        url: "https://example.com",
      },
    });

    render(<Inference />);

    const input = screen.getByPlaceholderText(
      "Enter a URL, e.g. https://example.com",
    );
    fireEvent.change(input, { target: { value: "https://example.com" } });

    const submitButton = screen.getByText("Submit");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(axios).toHaveBeenCalledWith(expect.objectContaining({
        method: "post",
        url: "http://localhost:5000/api/v1/logres",
        data: { url: "https://example.com" },
      }));
      expect(InferenceResult).toHaveBeenCalledWith(
        { props: expect.objectContaining({ message: "Malicious website!" }) },
        {},
      );
    });
  });

  test("handles invalid URL error", async () => {
    (axios as vi.Mocked<typeof axios>).mockRejectedValue(
      new Error("Invalid URL"),
    );

    render(<Inference />);

    const input = screen.getByPlaceholderText(
      "Enter a URL, e.g. https://example.com",
    );
    fireEvent.change(input, { target: { value: "invalid-url" } });

    const submitButton = screen.getByText("Submit");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("URL is invalid")).toBeInTheDocument();
    });
  });
});
