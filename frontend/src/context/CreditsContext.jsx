import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { supabase } from '../lib/supabase'

const CreditsContext = createContext({})

export function CreditsProvider({ children }) {
  const { user } = useAuth()
  const [credits, setCredits] = useState(null)
  const [freeScanUsed, setFreeScanUsed] = useState(false)
  const [totalScans, setTotalScans] = useState(0)
  const [loaded, setLoaded] = useState(false)

  const refreshCredits = useCallback(async () => {
    if (!user) {
      setCredits(null)
      setFreeScanUsed(false)
      setTotalScans(0)
      setLoaded(false)
      return
    }
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('scan_credits, free_scan_used, total_scans')
        .eq('user_id', user.id)
        .single()
      if (data && !error) {
        setCredits(data.scan_credits)
        setFreeScanUsed(data.free_scan_used)
        setTotalScans(data.total_scans)
      } else {
        // Profile doesn't exist yet (table not migrated, or new user before trigger runs)
        // Default: assume free scan is available
        setCredits(0)
        setFreeScanUsed(false)
        setTotalScans(0)
      }
    } catch {
      // Table might not exist yet — default to free scan available
      setCredits(0)
      setFreeScanUsed(false)
      setTotalScans(0)
    }
    setLoaded(true)
  }, [user])

  useEffect(() => { refreshCredits() }, [refreshCredits])

  // User can scan if: they have credits, OR they haven't used their free scan
  const canScan = user ? (!loaded ? true : credits > 0 || !freeScanUsed) : false

  return (
    <CreditsContext.Provider value={{ credits, freeScanUsed, totalScans, canScan, loaded, refreshCredits }}>
      {children}
    </CreditsContext.Provider>
  )
}

export const useCredits = () => useContext(CreditsContext)
