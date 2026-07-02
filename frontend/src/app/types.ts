export type UserRole = 'patient' | 'doctor' | 'nurse' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  active?: boolean;
  patientReference?: string | null;
  jobTitle?: string | null;
  department?: string | null;
  phoneExtension?: string | null;
}

export interface SessionResponse {
  ok: boolean;
  user: User | null;
  unreadCount: number;
}

export interface LoginResponse {
  ok: boolean;
  user: User;
  unreadCount: number;
}

export interface RegisterResponse {
  ok: boolean;
  user: User;
}
