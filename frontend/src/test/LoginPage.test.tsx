import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../app/AppContext', () => ({
  useApp: vi.fn(),
}));

import { useApp } from '../app/AppContext';
import { LoginPage } from '../app/components/LoginPage';

const mockedUseApp = vi.mocked(useApp);

function makeContext(overrides: Record<string, unknown> = {}) {
  return {
    login: vi.fn().mockResolvedValue(undefined),
    setCurrentPage: vi.fn(),
    setPendingVerificationEmail: vi.fn(),
    ...overrides,
  } as any;
}

describe('LoginPage', () => {
  beforeEach(() => {
    mockedUseApp.mockReturnValue(makeContext());
  });

  test('submits the entered email and password through the app login function', async () => {
    const user = userEvent.setup();
    const login = vi.fn().mockResolvedValue(undefined);
    mockedUseApp.mockReturnValue(makeContext({ login }));
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email address/i), 'patient@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'PatientPass123!');
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(login).toHaveBeenCalledWith('patient@example.com', 'PatientPass123!');
  });

  test('allows the password field to be shown and hidden', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);
    const password = screen.getByLabelText(/^password$/i);

    expect(password).toHaveAttribute('type', 'password');
    await user.click(screen.getByRole('button', { name: /show password/i }));
    expect(password).toHaveAttribute('type', 'text');
    await user.click(screen.getByRole('button', { name: /hide password/i }));
    expect(password).toHaveAttribute('type', 'password');
  });

  test('shows a verification error and stores the pending email when login requires verification', async () => {
    const user = userEvent.setup();
    const setPendingVerificationEmail = vi.fn();
    const login = vi.fn().mockRejectedValue(new Error('Please verify your email before signing in.'));
    mockedUseApp.mockReturnValue(makeContext({ login, setPendingVerificationEmail }));
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email address/i), 'VERIFY@EXAMPLE.COM');
    await user.type(screen.getByLabelText(/^password$/i), 'PatientPass123!');
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByText(/please verify your email/i)).toBeInTheDocument();
    expect(setPendingVerificationEmail).toHaveBeenCalledWith('VERIFY@EXAMPLE.COM');
    expect(screen.getByRole('button', { name: /verify email otp/i })).toBeInTheDocument();
  });

  test('navigates to the forgot-password page', async () => {
    const user = userEvent.setup();
    const setCurrentPage = vi.fn();
    mockedUseApp.mockReturnValue(makeContext({ setCurrentPage }));
    render(<LoginPage />);

    await user.click(screen.getByRole('button', { name: /forgot password/i }));

    expect(setCurrentPage).toHaveBeenCalledWith('forgot-password');
  });
});
