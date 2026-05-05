"""Cloud Run Web Server for Agentic Security Auditor v2.0 (ADK)."""

import os
import sys
import json
import asyncio
from flask import Flask, request, jsonify

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Force Vertex AI for ADK
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0679032909")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

app = Flask(__name__)

# ─── Legacy endpoints (v1 compatibility) ───

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'agentic-security-auditor',
        'version': '2.0.0',
        'adk_enabled': True
    })

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'Agentic Security Auditor v2.0',
        'version': '2.0.0',
        'endpoints': {
            '/health': 'Health check',
            '/audit': 'POST - Legacy audit (static + Slither + AI)',
            '/v2/audit': 'POST - ADK multi-agent audit',
            '/v2/audit/address': 'POST - ADK audit by contract address',
            '/v2/audit/code': 'POST - ADK audit by code',
        }
    })

@app.route('/audit', methods=['POST'])
def legacy_audit():
    """Legacy v1 audit endpoint (backward compatible)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400
        
        code = data.get('code', '')
        address = data.get('address', '')
        chain = data.get('chain', 'ethereum')
        
        if not code and not address:
            return jsonify({'error': 'Provide either "code" or "address"'}), 400
        
        from tools.audit_tools import analyze_contract_code
        from tools.vulnerability_db import enrich_finding
        
        results = {
            'static': {'findings': [], 'risk_score': 0},
            'slither': {'success': False, 'findings': []},
            'ai': {'enabled': False, 'report': ''},
        }
        
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
        
        static_result = analyze_contract_code(code)
        results['static'] = {'findings': static_result.get('findings', []), 'risk_score': static_result.get('risk_score', 0)}
        
        try:
            from tools.slither_integration import run_slither_analysis
            slither_result = run_slither_analysis(code)
            if slither_result.get('success'):
                slither_result['findings'] = [enrich_finding(f) for f in slither_result['findings']]
                results['slither'] = slither_result
        except Exception:
            pass
        
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if api_key:
            try:
                from core.openrouter_client import get_openrouter_client
                client = get_openrouter_client()
                ai_report = client.audit_contract(code)
                results['ai'] = {'enabled': True, 'report': ai_report}
            except Exception as e:
                results['ai'] = {'enabled': False, 'error': str(e)}
        
        risk_score = results['static'].get('risk_score', 0)
        total_findings = len(results['static']['findings']) + len(results['slither'].get('findings', []))
        
        return jsonify({
            'status': 'success',
            'version': '1.0',
            'risk_score': risk_score,
            'total_findings': total_findings,
            'results': results,
        })
        
    except Exception as e:
        return jsonify({'error': f'Audit failed: {type(e).__name__}: {e}'}), 500


# ─── ADK v2 endpoints ───

@app.route('/v2/audit/address', methods=['POST'])
def v2_audit_address():
    """ADK v2: Audit a deployed contract address."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400
        
        address = data.get('address', '')
        chain = data.get('chain', 'ethereum')
        
        if not address:
            return jsonify({'error': 'Provide "address"'}), 400
        
        from agent_v2 import ADKSecurityAuditor
        auditor = ADKSecurityAuditor()
        result = asyncio.run(auditor.audit_address(address, chain))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'status': 'success',
            'version': '2.0',
            'contract_name': result.get('contract_name', 'Unknown'),
            'address': address,
            'chain': chain,
            'report': result.get('report', ''),
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'ADK audit failed: {type(e).__name__}: {e}', 'trace': traceback.format_exc()}), 500

@app.route('/v2/audit/code', methods=['POST'])
def v2_audit_code():
    """ADK v2: Audit raw Solidity code."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400
        
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'Provide "code"'}), 400
        
        from agent_v2 import ADKSecurityAuditor
        auditor = ADKSecurityAuditor()
        result = asyncio.run(auditor.audit_code(code))
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'status': 'success',
            'version': '2.0',
            'code_length': len(code),
            'report': result.get('report', ''),
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'ADK audit failed: {type(e).__name__}: {e}', 'trace': traceback.format_exc()}), 500

@app.route('/v2/audit', methods=['POST'])
def v2_audit():
    """ADK v2: Smart routing — auto-detects address vs code."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400
        
        address = data.get('address', '')
        code = data.get('code', '')
        chain = data.get('chain', 'ethereum')
        
        from agent_v2 import ADKSecurityAuditor
        auditor = ADKSecurityAuditor()
        
        if address:
            result = asyncio.run(auditor.audit_address(address, chain))
        elif code:
            result = asyncio.run(auditor.audit_code(code))
        else:
            return jsonify({'error': 'Provide either "address" or "code"'}), 400
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'status': 'success',
            'version': '2.0',
            'report': result.get('report', ''),
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'ADK audit failed: {type(e).__name__}: {e}', 'trace': traceback.format_exc()}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
