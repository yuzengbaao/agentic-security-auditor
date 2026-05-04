"""Cloud Run Web Server for Agentic Security Auditor."""

import os
import sys
import json
from flask import Flask, request, jsonify, send_file
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'agentic-security-auditor',
        'version': '0.2.1'
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with service info."""
    return jsonify({
        'service': 'Agentic Security Auditor',
        'version': '0.2.1',
        'endpoints': {
            '/health': 'Health check',
            '/audit': 'POST - Audit a smart contract',
            '/audit/file': 'POST - Audit a Solidity file',
        }
    })

@app.route('/audit', methods=['POST'])
def audit():
    """Audit a smart contract from code or address."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400
        
        code = data.get('code', '')
        address = data.get('address', '')
        chain = data.get('chain', 'ethereum')
        
        if not code and not address:
            return jsonify({'error': 'Provide either "code" or "address"'}), 400
        
        # Import audit pipeline
        from tools.audit_tools import analyze_contract_code
        from tools.vulnerability_db import enrich_finding
        
        results = {
            'static': {'findings': [], 'risk_score': 0},
            'slither': {'success': False, 'findings': []},
            'ai': {'enabled': False, 'report': ''},
        }
        
        # Get code
        if address and not code:
            try:
                from utils.etherscan_fetcher import fetch_contract_code
                fetch_result = fetch_contract_code(address, chain)
                if fetch_result.get('success'):
                    code = fetch_result['code']
                else:
                    return jsonify({'error': f"Failed to fetch contract: {fetch_result.get('error')}"}), 400
            except Exception as e:
                return jsonify({'error': f"Etherscan fetch failed: {e}"}), 500
        
        if not code:
            return jsonify({'error': 'No code to audit'}), 400
        
        # Phase 1: Static Analysis
        static_result = analyze_contract_code(code)
        results['static'] = {'findings': static_result.get('findings', []), 'risk_score': static_result.get('risk_score', 0)}
        
        # Phase 2: Slither (if available)
        try:
            from tools.slither_integration import run_slither_analysis
            slither_result = run_slither_analysis(code)
            if slither_result.get('success'):
                slither_result['findings'] = [enrich_finding(f) for f in slither_result['findings']]
                results['slither'] = slither_result
        except Exception:
            pass
        
        # Phase 3: AI Audit (if API key available)
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if api_key:
            try:
                from core.openrouter_client import get_openrouter_client
                client = get_openrouter_client()
                ai_report = client.audit_contract(code)
                results['ai'] = {'enabled': True, 'report': ai_report}
            except Exception as e:
                results['ai'] = {'enabled': False, 'error': str(e)}
        
        # Calculate final risk score
        risk_score = results['static'].get('risk_score', 0)
        total_findings = len(results['static']['findings']) + len(results['slither'].get('findings', []))
        
        return jsonify({
            'status': 'success',
            'risk_score': risk_score,
            'total_findings': total_findings,
            'results': results,
        })
        
    except Exception as e:
        return jsonify({'error': f'Audit failed: {type(e).__name__}: {e}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
