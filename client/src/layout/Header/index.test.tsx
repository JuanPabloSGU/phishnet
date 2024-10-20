import { render, screen } from "@tests/test-utils";
import Header from "./index"; // Adjust the path as necessary
import "@testing-library/jest-dom"; // For custom matchers
import userEvent from "@testing-library/user-event";

test("renders Header with correct navigation and links", () => {
  render(
    <Header />,
  );

  // Check if the title "Phishnet" is rendered
  const headerTitle = screen.getByText(/Phishnet/i);
  expect(headerTitle).toBeInTheDocument();

  // Check that the links are rendered
  const homeLink = screen.getByText(/Home/i);
  expect(homeLink).toBeInTheDocument();
  expect(homeLink).toHaveAttribute("href", "/");

  const aboutLink = screen.getByText(/About/i);
  expect(aboutLink).toBeInTheDocument();
  expect(aboutLink).toHaveAttribute("href", "/about");

  const contactLink = screen.getByText(/Contact/i);
  expect(contactLink).toBeInTheDocument();
  expect(contactLink).toHaveAttribute("href", "/contact");

  const loginLink = screen.getByText(/Login/i);
  expect(loginLink).toBeInTheDocument();
  expect(loginLink).toHaveAttribute("href", "/login");
});


test("handles active state when a link is clicked", async () => {
  render(
    <Header />,
  );

  // Simulate clicking the "About" link
  const aboutLink = screen.getByText(/About/i);
  await userEvent.click(aboutLink);

  // wait for the state to update

  // Check if the "About" link is marked as active
  expect(aboutLink.closest("a")?.parentNode).toHaveAttribute("data-active", "true");
});

test("default route is home", () => {
  render(
    <Header />,
  );

  // Simulate clicking the "About" link
  const aboutLink = screen.getByText(/Home/i);

  // wait for the state to update

  // Check if the "About" link is marked as active
  expect(aboutLink.closest("a")?.parentNode).toHaveAttribute("data-active", "true");
});
