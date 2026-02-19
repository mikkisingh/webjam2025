import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://wqnepenlpwtxbqufkjoz.supabase.co'
const supabaseAnonKey = 'sb_publishable_usQYaaKtqbxIhHJi1VypOw_jTL_WFWR'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
