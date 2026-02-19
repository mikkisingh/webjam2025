import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { supabase } from '../lib/supabase'

const CreditsContext = createContext({})

export function CreditsProvider({ children }) {
  const { user } = useAuth()
  const [credits, setCredits] = useState(null)
  const [freeScanUsed, setFreeScanUsed] = useState(false)
  const [totalScans, setTotalScans] = useState(0)

  const refreshCredits = useCallback(async () => {
    if (!user) {
      setCredits(null)
      setFreeScanUsed(false)
      setTotalScans(0)
      return
    }
    const { data } = await supabase
      .from('profiles')
      .select('scan_credits, free_scan_used, total_scans')
      .eq('user_id', user.id)
      .single()
    if (data) {
      setCredits(data.scan_credits)
      setFreeScanUsed(data.free_scan_used)
      setTotalScans(data.total_scans)
    }
  }, [user])

  useEffect(() => { refreshCredits() }, [refreshCredits])

  const canScan = user && (credits === null ? false : credits > 0 || !freeScanUsed)

  return (
    <CreditsContext.Provider value={{ credits, freeScanUsed, totalScans, canScan, refreshCredits }}>
      {children}
    </CreditsContext.Provider>
  )
}

export const useCredits = () => useContext(CreditsContext)
