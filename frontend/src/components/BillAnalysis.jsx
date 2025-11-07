import { useState, useEffect } from 'react';

function BillAnalysis({ billId }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [billData, setBillData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (billId) {
      analyzeBill();
    }
  }, [billId]);

  const analyzeBill = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      // Trigger analysis
      const analyzeResponse = await fetch(`http://localhost:5000/analyze/${billId}`, {
        method: 'POST',
      });

      const analyzeData = await analyzeResponse.json();

      if (!analyzeResponse.ok) {
        throw new Error(analyzeData.error || 'Analysis failed');
      }

      setBillData(analyzeData);
      setAnalyzed(true);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getSeverityClass = (severity) => {
    const severityMap = {
      low: 'severity-low',
      medium: 'severity-medium',
      high: 'severity-high',
    };
    return severityMap[severity?.toLowerCase()] || 'severity-low';
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  if (analyzing) {
    return (
      <div className="bill-analysis analyzing">
        <div className="loading-spinner">⏳</div>
        <h3>Analyzing your bill...</h3>
        <p>This may take a few moments as we examine charges and identify potential issues.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bill-analysis error">
        <div className="error-icon">⚠️</div>
        <h3>Analysis Error</h3>
        <p>{error}</p>
        <button className="button" onClick={analyzeBill}>
          Try Again
        </button>
      </div>
    );
  }

  if (!analyzed || !billData) {
    return null;
  }

  const { structured_data, analysis_results, summary, complaint_email } = billData;

  return (
    <div className="bill-analysis">
      <h2>Analysis Results</h2>

      {/* Summary Section */}
      <section className="analysis-section summary-section">
        <h3>Summary</h3>
        <p className="summary-text">{summary}</p>
      </section>

      {/* Bill Details */}
      <section className="analysis-section details-section">
        <h3>Bill Details</h3>
        <div className="details-grid">
          <div className="detail-item">
            <span className="detail-label">Patient:</span>
            <span className="detail-value">{structured_data.patient_name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Provider:</span>
            <span className="detail-value">{structured_data.provider_name}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Date of Service:</span>
            <span className="detail-value">{structured_data.date_of_service}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Insurance:</span>
            <span className="detail-value">{structured_data.insurance_info}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Amount:</span>
            <span className="detail-value total-amount">
              ${structured_data.total?.toFixed(2) || '0.00'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Patient Responsibility:</span>
            <span className="detail-value patient-resp">
              ${structured_data.patient_responsibility?.toFixed(2) || '0.00'}
            </span>
          </div>
        </div>
      </section>

      {/* Charges Breakdown */}
      <section className="analysis-section charges-section">
        <h3>Charges Breakdown</h3>
        <div className="charges-table">
          <table>
            <thead>
              <tr>
                <th>Item/Service</th>
                <th>Code</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {structured_data.charges?.map((charge, index) => (
                <tr key={index}>
                  <td>{charge.item}</td>
                  <td>{charge.code || 'N/A'}</td>
                  <td className="charge-cost">${charge.cost?.toFixed(2) || '0.00'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Issues Found */}
      <section className="analysis-section issues-section">
        <h3>
          Issues Detected
          <span className={`severity-badge ${getSeverityClass(analysis_results.overall_severity)}`}>
            {analysis_results.overall_severity?.toUpperCase() || 'NONE'}
          </span>
        </h3>

        {analysis_results.issues?.length > 0 ? (
          <div className="issues-list">
            {analysis_results.issues.map((issue, index) => (
              <div key={index} className={`issue-item ${getSeverityClass(issue.severity)}`}>
                <div className="issue-header">
                  <span className="issue-type">{issue.type}</span>
                  <span className={`issue-severity ${getSeverityClass(issue.severity)}`}>
                    {issue.severity}
                  </span>
                </div>
                <p className="issue-description">{issue.description}</p>
                {issue.item && <p className="issue-item-name">Affected: {issue.item}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="no-issues">✅ No issues detected. Your bill appears to be in order.</p>
        )}

        {analysis_results.potential_savings > 0 && (
          <div className="potential-savings">
            <h4>Potential Savings</h4>
            <p className="savings-amount">
              ${analysis_results.potential_savings?.toFixed(2)}
            </p>
          </div>
        )}
      </section>

      {/* Recommendations */}
      {analysis_results.recommendations?.length > 0 && (
        <section className="analysis-section recommendations-section">
          <h3>Recommendations</h3>
          <ul className="recommendations-list">
            {analysis_results.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Complaint Email Template */}
      {complaint_email && (
        <section className="analysis-section email-section">
          <h3>Dispute Email Template</h3>
          <p className="email-hint">
            Copy this email and send it to your provider's billing department:
          </p>
          <div className="email-template">
            <pre>{complaint_email}</pre>
          </div>
          <button
            className="button primary"
            onClick={() => copyToClipboard(complaint_email)}
          >
            📋 Copy Email Template
          </button>
        </section>
      )}
    </div>
  );
}

export default BillAnalysis;
