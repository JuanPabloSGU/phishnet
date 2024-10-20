import { render, screen } from "@tests/test-utils";
import InferenceResult from "./index";

describe("InferenceResult Component", () => {
  const mockProps = {
    props: {
      url: "https://example.com",
      value: [0.85], // 85% confidence
      message: "Malicious website!",
    },
  };



  test("renders component correctly", () => {
    render(<InferenceResult {...mockProps} />);

    // Check if the URL is displayed
    expect(screen.getByText("URL searched: https://example.com")).toBeInTheDocument();

    // Check if the percentage value is displayed correctly
    expect(screen.getByText("85%")).toBeInTheDocument();

    // Check if the message is displayed
    expect(screen.getByText("Malicious website!")).toBeInTheDocument();
  });

  test("renders ring progress with correct value", () => {
    render(<InferenceResult {...mockProps} />);

    // Since the value is 0.85 (85%), check if the progress bar reflects this percentage
    const ringProgress = screen.getByText("85%");
    expect(ringProgress).toBeInTheDocument();
  });

  test("handles different confidence values correctly", () => {
    const lowConfidenceProps = {
      props: {
        url: "https://low-confidence.com",
        value: [0.15], // 15% confidence
        message: "Non Malicious website!",
      },
    };

    render(<InferenceResult {...lowConfidenceProps} />);

    // Check the ring progress and message for a lower confidence result
    expect(screen.getByText("15%")).toBeInTheDocument();
    expect(screen.getByText("Non Malicious website!")).toBeInTheDocument();
  });
});

