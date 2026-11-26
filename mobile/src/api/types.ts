export enum UserRole {
  STUDENT = 'STUDENT',
  ADMIN = 'ADMIN',
  PLACEMENT_CELL = 'PLACEMENT_CELL',
}

export interface StudentProfile {
  id: string;
  institution?: string | null;
  department?: string | null;
  batch_year?: number | null;
  cgpa?: number | null;
  skills?: string | null;
  career_preferences?: string | null;
  readiness_score: number;
}

export interface Role {
  id: string;
  name: string;
  description?: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
  roles: Role[];
  student_profile?: StudentProfile | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface StudentRegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone_number?: string;
  institution?: string;
  department?: string;
  batch_year?: number;
}

export interface RefreshTokenPayload {
  refresh_token: string;
}

export interface ApiErrorResponse {
  detail?: string | { msg?: string }[] | Record<string, unknown>;
  message?: string;
}
