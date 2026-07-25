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
  specialisation?: string;
  location?: string;
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

export type AppointmentStatus = 'Booked' | 'Pending Approval' | 'Completed' | 'Cancelled' | 'Missed' | 'Rejected';
export type PrescriptionStatus = 'Requested' | 'Under Review' | 'Approved' | 'Ready for Collection' | 'Collected' | 'Rejected';
export type PaymentStatus = 'Not required' | 'Pending' | 'Paid';

export interface Appointment {
  id: string;
  patientName: string;
  doctorName: string;
  doctorRole: 'Doctor' | 'Nurse';
  specialisation: string;
  date: string;
  time: string;
  reason: string;
  status: AppointmentStatus;
  duration: number;
}

export interface Prescription {
  id: string;
  patientName: string;
  medicine: string;
  quantity: string;
  reason: string;
  requestedDate: string;
  status: PrescriptionStatus;
  paymentStatus: PaymentStatus;
  reviewedBy?: string;
  amountDue?: number;
  paymentReference?: string | null;
}

export interface Notification {
  id: string;
  type: 'appointment_booked' | 'appointment_cancelled' | 'prescription_approved' | 'prescription_ready' | 'payment_received' | string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export interface StaffMember {
  id: string;
  name: string;
  role: 'Doctor' | 'Nurse';
  specialisation: string;
  email: string;
  status: 'Verified' | 'Pending' | 'Rejected' | string;
  licenceNumber: string;
}

export interface AvailabilitySlot {
  id: string;
  staffId: string;
  staffName: string;
  date: string;
  time: string;
  duration: number;
  booked: boolean;
  role?: 'Doctor' | 'Nurse';
  specialisation?: string;
  location?: string;
}


export interface StaffAvailabilityGeneratedSlot {
  id: string;
  startTime: string;
  endTime: string;
  status: 'Available' | 'Booked' | 'Pending Approval' | string;
}

export interface StaffAvailabilityBlock {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  slotDuration: number;
  location: string;
  slotCount: number;
  canEdit: boolean;
  slots: StaffAvailabilityGeneratedSlot[];
}

export type Page =
  | 'landing'
  | 'login'
  | 'register'
  | 'patient-dashboard'
  | 'book-appointment'
  | 'appointment-history'
  | 'patient-profile'
  | 'prescription-request'
  | 'prescription-history'
  | 'prescription-payment'
  | 'doctor-dashboard'
  | 'doctor-schedule'
  | 'doctor-availability'
  | 'doctor-prescriptions'
  | 'nurse-dashboard'
  | 'nurse-schedule'
  | 'nurse-availability'
  | 'admin-dashboard'
  | 'admin-users'
  | 'admin-appointments'
  | 'admin-prescriptions'
  | 'admin-reports'
  | 'admin-audit'
  | 'notifications';
