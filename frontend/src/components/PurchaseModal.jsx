import { useState } from 'react'
import { API_URL } from '../lib/api'
import { supabase } from '../lib/supabase'

const PLANS = [
  {
    name: '1 Scan',
    price: '$0.99',
    perScan: '$0.99/scan',
    priceId: import.meta.env.VITE_STRIPE_PRICE_SINGLE,
    credits: 1,
  },
  {
    name: '5-Pack',
    price: '$4.49',
    perScan: '$0.90/scan',
    priceId: import.meta.env.VITE_STRIPE_PRICE_5PACK,
    credits: 5,
    popular: true,
    savings: 'Save 10%',
  },
  {
    name: '20-Pack',
    price: '$14.99',
    perScan: '$0.75/scan',
    priceId: import.meta.env.VITE_STRIPE_PRICE_20PACK,
    credits: 20,
    savings: 'Best value',
  },
]

export default function PurchaseModal({ isOpen, onClose }) {
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState(null)

  const handlePurchase = async (priceId) => {
    setLoading(priceId)
    setError(null)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const resp = await fetch(`${API_URL}/stripe/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ price_id: priceId }),
      })
      const data = await resp.json()
      if (data.checkout_url) {
        window.location.href = data.checkout_url
      } else {
        setError(data.error || 'Something went wrong. Please try again.')
      }
    } catch {
      setError('Payment service unavailable. Please try again.')
    } finally {
      setLoading(null)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content purchase-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        <h2 className="purchase-title">Get Scan Credits</h2>
        <p className="muted purchase-subtitle">
          Each credit lets you analyze one medical bill with AI-powered insights.
        </p>

        {error && <p className="purchase-error">{error}</p>}

        <div className="pricing-cards">
          {PLANS.map((plan) => (
            <div key={plan.priceId} className={`pricing-card ${plan.popular ? 'pricing-card--popular' : ''}`}>
              {plan.savings && <span className="pricing-badge">{plan.savings}</span>}
              <h3 className="pricing-name">{plan.name}</h3>
              <div className="pricing-amount">{plan.price}</div>
              <div className="pricing-per-scan">{plan.perScan}</div>
              <button
                className={`button ${plan.popular ? 'primary' : 'ghost'} pricing-buy-btn`}
                onClick={() => handlePurchase(plan.priceId)}
                disabled={loading !== null}
              >
                {loading === plan.priceId ? 'Redirecting...' : 'Buy Now'}
              </button>
            </div>
          ))}
        </div>

        <p className="muted purchase-footer">
          Secure payment via Stripe. Credits never expire.
        </p>
      </div>
    </div>
  )
}
