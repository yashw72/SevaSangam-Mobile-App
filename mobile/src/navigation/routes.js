/**
 * SevaSangam Mobile App - Route Constants
 * 
 * Central registry of all navigation route names across Auth, Customer,
 * Worker, Admin, and Shared navigators. No magic strings in downstream navigation.
 */

export const ROUTES = {
  // Navigators / Root Containers
  ROOT: {
    AUTH_NAVIGATOR: 'AuthNavigator',
    CUSTOMER_NAVIGATOR: 'CustomerNavigator',
    WORKER_NAVIGATOR: 'WorkerNavigator',
    WORKER_ACCOUNT_STATUS: 'WorkerAccountStatus',
    ADMIN_NAVIGATOR: 'AdminNavigator',
  },

  // Auth Navigator Screens (Section 11)
  AUTH: {
    SPLASH: 'Splash',
    LANGUAGE_SELECT: 'LanguageSelect',
    ONBOARDING: 'Onboarding',
    LOGIN: 'Login',
    VERIFY_OTP: 'VerifyOtp',
    ROLE_SELECT: 'RoleSelect',
    WORKER_ACCOUNT_STATUS: 'WorkerAccountStatus',
  },

  // Customer Navigator Tabs & Screens (Section 8)
  CUSTOMER: {
    // Tabs
    HOME_TAB: 'CustomerHomeTab',
    BOOKINGS_TAB: 'CustomerBookingsTab',
    NOTIFICATIONS_TAB: 'CustomerNotificationsTab',
    PROFILE_TAB: 'CustomerProfileTab',

    // Stacks & Screens
    HOME: 'CustomerHome',
    SERVICE_CATEGORY: 'ServiceCategory',
    WORKER_LIST: 'WorkerList',
    WORKER_PROFILE: 'WorkerProfile',
    BOOKING_FLOW: 'BookingFlow',
    EMERGENCY_BOOKING: 'EmergencyBooking',
    BOOKING_TRACKING: 'BookingTracking',
    BOOKING_DETAIL: 'CustomerBookingDetail',
    BOOKING_HISTORY: 'BookingHistory',
    RATE_REVIEW: 'RateReview',
    NOTIFICATIONS: 'CustomerNotifications',
    PROFILE: 'CustomerProfile',
    SAVED_ADDRESSES: 'SavedAddresses',
    HELP_COMPLAINT: 'HelpComplaint',
  },

  // Worker Navigator Tabs & Screens (Section 9)
  WORKER: {
    // Tabs
    HOME_TAB: 'WorkerHomeTab',
    JOBS_TAB: 'WorkerJobsTab',
    EARNINGS_TAB: 'WorkerEarningsTab',
    PROFILE_TAB: 'WorkerProfileTab',

    // Stacks & Screens
    HOME: 'WorkerHome',
    JOB_REQUESTS: 'JobRequests',
    ACTIVE_JOB: 'ActiveJob',
    JOB_HISTORY: 'JobHistory',
    EARNINGS: 'WorkerEarnings',
    REVIEWS: 'WorkerReviews',
    PROFILE: 'WorkerProfile',
    SKILLS_EDIT: 'WorkerSkillsEdit',
    CERTIFICATES: 'WorkerCertificates',
    WELFARE_CARD: 'WorkerWelfareCard',
    ACCOUNT_STATUS: 'WorkerAccountStatus',
    NOTIFICATIONS: 'WorkerNotifications',
    SETTINGS: 'WorkerSettings',
    HELP: 'WorkerHelp',
  },

  // Admin Navigator Tabs & Screens (Section 10)
  ADMIN: {
    // Tabs
    OVERVIEW_TAB: 'AdminOverviewTab',
    WORKERS_TAB: 'AdminWorkersTab',
    BOOKINGS_TAB: 'AdminBookingsTab',
    COMPLAINTS_TAB: 'AdminComplaintsTab',
    MORE_TAB: 'AdminMoreTab',

    // Stacks & Screens
    OVERVIEW: 'AdminOverview',
    VERIFICATION_QUEUE: 'VerificationQueue',
    VERIFICATION_DETAIL: 'VerificationDetail',
    WORKERS_DIRECTORY: 'WorkersDirectory',
    WORKER_DETAIL: 'WorkerDetailAdmin',
    BOOKINGS_MONITOR: 'BookingsMonitor',
    BOOKING_DETAIL: 'BookingDetailAdmin',
    FAIR_DISTRIBUTION: 'FairDistribution',
    COMPLAINTS: 'AdminComplaints',
    COMPLAINT_DETAIL: 'ComplaintDetail',
    ANALYTICS_FORECAST: 'AnalyticsForecast',
    WELFARE_PROGRAMS: 'WelfarePrograms',
    WELFARE_PROGRAM_CREATE: 'WelfareProgramCreate',
    NOTIFICATIONS: 'AdminNotifications',
    SETTINGS: 'AdminSettings',
  },

  // Shared Screens
  SHARED: {
    NOTIFICATIONS: 'Notifications',
    SETTINGS: 'Settings',
    HELP: 'Help',
    NOT_FOUND: 'NotFound',
  },
};

export default ROUTES;
