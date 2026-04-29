/**
 * Tipos TypeScript para EspinarGo Admin
 * Coinciden con los schemas del backend (Módulo 4)
 */

export type UserRole = 'passenger' | 'driver' | 'admin';
export type UserStatus = 'pending' | 'active' | 'suspended' | 'banned';
export type DriverStatus = 'pending_docs' | 'under_review' | 'approved' | 'rejected' | 'suspended';
export type TripStatus = 'searching' | 'negotiating' | 'accepted' | 'in_progress' | 'completed' | 'cancelled';
export type PackageStatus = 'pending' | 'assigned' | 'picked_up' | 'in_transit' | 'delivered' | 'cancelled';

export interface User {
  id: string;
  full_name: string;
  phone_number: string;
  email?: string;
  role: UserRole;
  status: UserStatus;
  phone_verified: boolean;
  email_verified?: boolean;
  avatar_url?: string;
  preferred_lang?: string;
  created_at: string;
  last_seen_at?: string;
}

export interface DriverProfile {
  id: string;
  user_id: string;
  vehicle_type?: 'mototaxi' | 'car';
  vehicle_brand?: string;
  vehicle_model?: string;
  vehicle_plate?: string;
  vehicle_color?: string;
  vehicle_year?: number;
  vehicle_seats?: number;
  vehicle_photo_url?: string;
  driver_status: DriverStatus;
  rating_display: number;
  total_trips: number;
  is_online: boolean;
  dni_front_url?: string;
  dni_back_url?: string;
  license_url?: string;
  soat_url?: string;
  property_card_url?: string;
  selfie_url?: string;
  approved_at?: string;
  rejection_reason?: string;
}

export interface Trip {
  id: string;
  passenger?: User;
  driver?: User;
  origin_address: string;
  dest_address: string;
  proposed_price: string;
  final_price?: string;
  status: TripStatus;
  payment_method: string;
  distance_km?: string;
  duration_minutes?: number;
  created_at: string;
  accepted_at?: string;
  started_at?: string;
  completed_at?: string;
  cancelled_at?: string;
}

export interface Package {
  id: string;
  tracking_code: string;
  sender?: User;
  driver?: User;
  recipient_name: string;
  recipient_phone: string;
  delivery_address: string;
  size: 'envelope' | 'small' | 'medium' | 'large';
  description: string;
  is_fragile: boolean;
  status: PackageStatus;
  price?: string;
  payment_method: string;
  created_at: string;
  picked_up_at?: string;
  delivered_at?: string;
}

export interface Rating {
  id: string;
  score: number;
  comment?: string;
  rating_type: 'passenger_to_driver' | 'driver_to_passenger';
  created_at: string;
  rater?: User;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  success?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DashboardStats {
  total_users: number;
  total_drivers: number;
  total_trips: number;
  total_packages: number;
  active_trips: number;
  pending_drivers: number;
  revenue_today: number;
  revenue_month: number;
}