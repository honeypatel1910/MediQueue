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
import { ForgotPasswordPage } from '../app/components/ForgotPasswordPage';

const mockedUseApp = vi.mocked(useApp);
const mockedPostJson = vi.mocked(postJson);

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    mockedUseApp.mockReturnValue({ setCurrentPage: vi.fn() } as any);
    mockedPostJson.mockReset();
  });

  test('requests a reset OTP using a normalised email address', async () => {
    const user = userEvent.setup();
    mockedPostJson.mockResolvedValue({ ok: true, message: 'Reset OTP sent.', emailSent: true } as any);
    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/registered email address/i), '  Patient@Test.COM  ');
    await user.click(screen.getByRole('button', { name: /send reset otp/i }));

    expect(mockedPostJson).toHaveBeenCalledWith('/api/password-reset/request', {
      email: 'patient@test.com',
    });
    expect(await screen.findByLabelText(/6-digit otp/i)).toBeInTheDocument();
  });

  test('validates mismatched new passwords after OTP verification', async () => {
    const user = userEvent.setup();
    mockedPostJson
      .mockResolvedValueOnce({ ok: true, message: 'OTP sent.', emailSent: true } as any)
      .mockResolvedValueOnce({ ok: true, message: 'OTP verified.' } as any);
    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/registered email address/i), 'patient@example.com');
    await user.click(screen.getByRole('button', { name: /send reset otp/i }));
    await user.type(await screen.findByLabelText(/6-digit otp/i), '123456');
    await user.click(screen.getByRole('button', { name: /^verify otp$/i }));

    await user.type(await screen.findByLabelText(/^new password$/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/retype new password/i), 'DifferentPassword123!');
    await user.click(screen.getByRole('button', { name: /^reset password$/i }));

    expect(screen.getByText('New password and retype password do not match.')).toBeInTheDocument();
    expect(mockedPostJson).toHaveBeenCalledTimes(2);
  });

  test('completes the full password-reset UI flow', async () => {
    const user = userEvent.setup();
    mockedPostJson
      .mockResolvedValueOnce({ ok: true, message: 'OTP sent.', emailSent: true } as any)
      .mockResolvedValueOnce({ ok: true, message: 'OTP verified.' } as any)
      .mockResolvedValueOnce({ ok: true, message: 'Password reset successfully.' } as any);
    render(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/registered email address/i), 'patient@example.com');
    await user.click(screen.getByRole('button', { name: /send reset otp/i }));
    await user.type(await screen.findByLabelText(/6-digit otp/i), '123456');
    await user.click(screen.getByRole('button', { name: /^verify otp$/i }));
    await user.type(await screen.findByLabelText(/^new password$/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/retype new password/i), 'NewPassword123!');
    await user.click(screen.getByRole('button', { name: /^reset password$/i }));

    expect(mockedPostJson).toHaveBeenNthCalledWith(3, '/api/password-reset/confirm', {
      email: 'patient@example.com',
      password: 'NewPassword123!',
      confirmPassword: 'NewPassword123!',
    });
    expect(await screen.findByRole('heading', { name: /password reset complete/i })).toBeInTheDocument();
    expect(screen.getByText('Password reset successfully.')).toBeInTheDocument();
  });
});
