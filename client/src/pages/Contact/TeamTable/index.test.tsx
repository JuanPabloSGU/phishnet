import { render, screen } from '@tests/test-utils';
import TeamTable from './index'; // Adjust the path as needed
import '@testing-library/jest-dom';  // For the custom matchers

test('renders the table with the correct data', () => {
  render(<TeamTable />);

  // Check if the table has the correct number of rows (there should be 5 employees)
  const rows = screen.getAllByRole('row');
  expect(rows).toHaveLength(6); // 5 data rows + 1 header row

  // Check that each name is rendered
  expect(screen.getByText(/Alfred Genadri/i)).toBeInTheDocument();
  expect(screen.getByText(/Adam Jasniewicz/i)).toBeInTheDocument();
  expect(screen.getByText(/Arunav Sinha/i)).toBeInTheDocument();
  expect(screen.getByText(/James Couture/i)).toBeInTheDocument();
  expect(screen.getByText(/Juan Pablo Sanchez Garcia/i)).toBeInTheDocument();

  // Check that the correct job titles are displayed
  expect(screen.getByText(/Designer/i)).toBeInTheDocument();
  expect(screen.getByText(/Manager/i)).toBeInTheDocument();

  // Check that the emails are displayed as buttons
  expect(screen.getByText(/agena036@uottawa.ca/i)).toBeInTheDocument();
  expect(screen.getByText(/ajasn076@uottawa.ca/i)).toBeInTheDocument();
  expect(screen.getByText(/asinh060@uottawa.ca/i)).toBeInTheDocument();
  expect(screen.getByText(/jcout071@uottawa.ca/i)).toBeInTheDocument();
  expect(screen.getByText(/jsanc016@uottawa.ca/i)).toBeInTheDocument();

  // Check the Badge colors based on the job
  const engineerBadges = screen.getAllByText('Engineer');
  engineerBadges.forEach(badge => {
    expect(badge.parentNode).toHaveStyle('--badge-bg: var(--mantine-color-blue-light)');
  });

  const designerBadge = screen.getByText('Designer');

  expect(designerBadge.parentNode).toHaveStyle('--badge-bg: var(--mantine-color-pink-light)');

  const managerBadge = screen.getByText('Manager');

  expect(managerBadge.parentNode).toHaveStyle('--badge-bg: var(--mantine-color-cyan-light)');
});

