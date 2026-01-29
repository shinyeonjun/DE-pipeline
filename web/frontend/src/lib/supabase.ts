/**
 * Supabase 클라이언트 (Realtime용)
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://domjmcwzbpmultinvomo.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRvbWptY3d6YnBtdWx0aW52b21vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4ODA2MTYsImV4cCI6MjA4MjQ1NjYxNn0.fExyQMjveFQYHUq4Y1oFkoGgJUkkPWCVPbB_GaCnZWw';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
});

