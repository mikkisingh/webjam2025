import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', height: '100vh', padding: 32, textAlign: 'center',
        }}>
          <h2 style={{ marginBottom: 12 }}>Something went wrong</h2>
          <p style={{ color: 'var(--muted)', marginBottom: 24, maxWidth: 480 }}>
            An unexpected error occurred. Please refresh the page to try again.
          </p>
          <button
            className="button primary"
            onClick={() => window.location.reload()}
          >
            Refresh Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
