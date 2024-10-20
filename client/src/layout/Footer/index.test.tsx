import { render, screen } from "@tests/test-utils";
import Footer from "./index"; // Adjust the path as necessary
import "@testing-library/jest-dom"; // For custom matchers

test("renders the Footer with correct links", () => {
  render(
    <Footer />,
  );

  // Check if the title "Phishnet" is displayed
  expect(screen.getByText(/Phishnet/i)).toBeInTheDocument();

  // Check that the links are rendered and point to the correct routes
  const aboutLink = screen.getByText(/About/i);
  expect(aboutLink).toBeInTheDocument();
  expect(aboutLink).toHaveAttribute("href", "/about");

  const contactLink = screen.getByText(/Contact/i);
  expect(contactLink).toBeInTheDocument();
  expect(contactLink).toHaveAttribute("href", "/contact");

  const loginLink = screen.getByText(/Login/i);
  expect(loginLink).toBeInTheDocument();
  expect(loginLink).toHaveAttribute("href", "/login");

  // Ensure the links have the appropriate class for styling
  const links = screen.getAllByRole("link");
  links.forEach((link) => {
    expect(link).toHaveClass("dimmed");
  });
});
