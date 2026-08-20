import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../app/AppContext', () => ({
  useApp: vi.fn(),
}));
vi.mock('../app/api', () => ({
  postJson: vi.fn(),
}));

import { useApp } from '../app/AppContext';
import { postJson } from '../app/api';
import { RegisterPage } from '../app/components/RegisterPage';

const mockedUseApp = vi.mocked(useApp);
const mockedPostJson = vi.mocked(postJson);

function context() {
  return {
    setCurrentPage: vi.fn(),
    setPendingVerificationEmail: vi.fn(),
  } as any;
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/first name/i), 'Jane');
  await user.type(screen.getByLabelText(/last name/i), 'Smith');
  await user.type(screen.getByLabelText(/email address/i), 'Jane.Smith@Example.com');
  await user.type(screen.getByLabelText(/phone number/i), '07700900000');
  await user.type(screen.getByLabelText(/home address/i), '12 High Street, Leicester');
  await user.type(screen.getByLabelText(/^password$/i), 'PatientPass123!');
  await user.type(screen.getByLabelText(/confirm password/i), 'PatientPass123!');
}

describe('RegisterPage', () => {
  beforeEach(() => {
    mockedUseApp.mockReturnValue(context());
    mockedPostJson.mockReset();
  });

  test('shows client-side validation errors without calling the backend', async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText('First name is required.')).toBeInTheDocument();
    expect(screen.getByText('Last name is required.')).toBeInTheDocument();
    expect(screen.getByText('Please enter a valid email address.')).toBeInTheDocument();
    expect(screen.getByText('Phone number is required.')).toBeInTheDocument();
    expect(screen.getByText('Address is required.')).toBeInTheDocument();
    expect(screen.getByText('Password must be at least 8 characters.')).toBeInTheDocument();
    expect(mockedPostJson).not.toHaveBeenCalled();
  });

  test('rejects mismatched passwords before registration is submitted', async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await fillValidForm(user);
    const confirm = screen.getByLabelText(/confirm password/i);
    await user.clear(confirm);
    await user.type(confirm, 'DifferentPass123!');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument();
    expect(mockedPostJson).not.toHaveBeenCalled();
  });

  test('successful registration stores the verification email and opens the OTP page', async () => {
    const user = userEvent.setup();
    const setCurrentPage = vi.fn();
    const setPendingVerificationEmail = vi.fn();
    mockedUseApp.mockReturnValue({ setCurrentPage, setPendingVerificationEmail } as any);
    mockedPostJson.mockResolvedValue({ ok: true, email: 'jane.smith@example.com' } as any);
    render(<RegisterPage />);

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(mockedPostJson).toHaveBeenCalledWith('/api/register', expect.objectContaining({
      firstName: 'Jane',
      lastName: 'Smith',
      email: 'Jane.Smith@Example.com',
    }));
    expect(setPendingVerificationEmail).toHaveBeenCalledWith('jane.smith@example.com');
    expect(setCurrentPage).toHaveBeenCalledWith('verify-email');
  });

  test('shows a backend registration error to the user', async () => {
    const user = userEvent.setup();
    mockedPostJson.mockRejectedValue(new Error('This email is already registered.'));
    render(<RegisterPage />);

    await fillValidForm(user);
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('This email is already registered.')).toBeInTheDocument();
  });
});
