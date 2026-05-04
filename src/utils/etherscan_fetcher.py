"""Fetch contract source code from Etherscan-like block explorers."""

import re
from typing import Optional, Dict

# Browser automation imports
from playwright.sync_api import sync_playwright

# Common block explorer URLs
EXPLORERS = {
    "ethereum": "https://etherscan.io/address/{}",
    "bsc": "https://bscscan.com/address/{}",
    "polygon": "https://polygonscan.com/address/{}",
    "arbitrum": "https://arbiscan.io/address/{}",
    "optimism": "https://optimistic.etherscan.io/address/{}",
    "base": "https://basescan.org/address/{}",
}


def fetch_contract_from_explorer(
    address: str,
    chain: str = "ethereum",
    headless: bool = True
) -> Dict[str, str]:
    """Fetch contract source from block explorer using browser automation.
    
    Returns:
        {"source_code": "...", "contract_name": "...", "compiler_version": "..."}
    """
    if chain not in EXPLORERS:
        return {"error": f"Unsupported chain: {chain}"}
    
    url = EXPLORERS[chain].format(address)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            # Navigate to contract page
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for contract code to load
            page.wait_for_timeout(3000)
            
            # Try to find the "Contract" tab and click it
            contract_tab = page.locator("text=Contract").first
            if contract_tab.is_visible():
                contract_tab.click()
                page.wait_for_timeout(2000)
            
            # Extract source code
            # Etherscan usually shows code in a <pre> or textarea
            code_selectors = [
                "pre.js-sourcecopyarea",
                "textarea#editor",
                "div#dividcode",
                "pre:has-text('pragma solidity')",
            ]
            
            source_code = None
            for selector in code_selectors:
                element = page.locator(selector).first
                if element.is_visible():
                    source_code = element.text_content()
                    break
            
            # Also try to get contract name
            contract_name = None
            name_selectors = [
                "h1.h4.font-weight-bold",
                "span.d-flex.align-items-center",
            ]
            for selector in name_selectors:
                element = page.locator(selector).first
                if element.is_visible():
                    text = element.text_content()
                    if text and len(text) > 0:
                        contract_name = text.strip()
                        break
            
            browser.close()
            
            if source_code:
                return {
                    "source_code": source_code,
                    "contract_name": contract_name or "Unknown",
                    "address": address,
                    "chain": chain,
                    "url": url,
                }
            else:
                return {
                    "error": "Could not extract source code. Contract may be unverified.",
                    "url": url,
                }
                
    except Exception as e:
        return {"error": f"Browser automation failed: {e}"}


def fetch_contract_etherscan_api(
    address: str,
    api_key: Optional[str] = None,
    chain: str = "ethereum"
) -> Dict[str, str]:
    """Fetch contract using Etherscan API (if key available)."""
    import requests
    
    api_urls = {
        "ethereum": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
        "polygon": "https://api.polygonscan.com/api",
        "arbitrum": "https://api.arbiscan.io/api",
        "optimism": "https://api-optimistic.etherscan.io/api",
        "base": "https://api.basescan.org/api",
    }
    
    if chain not in api_urls:
        return {"error": f"Unsupported chain: {chain}"}
    
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
    }
    if api_key:
        params["apikey"] = api_key
    
    try:
        response = requests.get(api_urls[chain], params=params, timeout=30)
        data = response.json()
        
        if data.get("status") == "1" and data.get("result"):
            result = data["result"][0]
            source = result.get("SourceCode", "")
            
            # Handle multi-file contracts (JSON wrapped)
            if source.startswith("{"):
                import json
                try:
                    parsed = json.loads(source)
                    if "sources" in parsed:
                        sources = parsed["sources"]
                        source = "\n\n".join(
                            v.get("content", "") for v in sources.values()
                        )
                except json.JSONDecodeError:
                    pass
            
            return {
                "source_code": source,
                "contract_name": result.get("ContractName", "Unknown"),
                "compiler_version": result.get("CompilerVersion", "Unknown"),
                "address": address,
                "chain": chain,
                "optimization": result.get("OptimizationUsed", "Unknown"),
            }
        else:
            return {
                "error": data.get("message", "API request failed"),
                "result": data.get("result"),
            }
    except Exception as e:
        return {"error": f"API request failed: {e}"}


if __name__ == "__main__":
    # Test with a known verified contract (Uniswap V2 Router)
    TEST_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    
    print(f"Testing API fetch for {TEST_ADDRESS}...")
    result = fetch_contract_etherscan_api(TEST_ADDRESS, chain="ethereum")
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ Contract: {result['contract_name']}")
        print(f"   Source code length: {len(result['source_code'])} chars")
        print(f"   First 200 chars: {result['source_code'][:200]}")
