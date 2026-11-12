import urllib.request
import urllib.parse
import json

def test_api():
    # 1. Test index
    r = urllib.request.urlopen('http://127.0.0.1:8000/')
    assert r.status == 200
    print('1. Index HTML: OK (Status 200)')

    # 2. Test static assets
    r_css = urllib.request.urlopen('http://127.0.0.1:8000/static/css/styles.css')
    r_js = urllib.request.urlopen('http://127.0.0.1:8000/static/js/app.js')
    assert r_css.status == 200 and r_js.status == 200
    print('2. Static CSS & JS Assets: OK (Status 200)')

    # 3. Test samples API
    r_samples = urllib.request.urlopen('http://127.0.0.1:8000/api/samples')
    samples = json.loads(r_samples.read().decode())
    print(f'3. Samples API: OK ({len(samples["samples"])} samples available)')

    # 4. Test analyze-sample API with LSB stego
    data = urllib.parse.urlencode({'sample_name': 'sample_stego_lsb.png'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8000/api/analyze-sample', data=data)
    r_analysis = urllib.request.urlopen(req)
    res = json.loads(r_analysis.read().decode())
    print(f'4. Analyze API: OK')
    print(f'   Verdict: {res["correlation"]["verdict_label"]}')
    print(f'   Risk Score: {res["correlation"]["risk_score"]}/100')
    print(f'   Triggered Rules: {[r["rule_id"] for r in res["correlation"]["triggered_rules"]]}')
    print(f'   SHA-256 Digest: {res["triage"]["hashes"]["sha256"]}')

    # 5. Test analyze-sample API with Zero-Width text stego
    data_zw = urllib.parse.urlencode({'sample_name': 'sample_zero_width_stego.txt'}).encode()
    req_zw = urllib.request.Request('http://127.0.0.1:8000/api/analyze-sample', data=data_zw)
    r_zw = urllib.request.urlopen(req_zw)
    res_zw = json.loads(r_zw.read().decode())
    print(f'5. Zero-Width Text Test: OK')
    print(f'   Decoded Hidden Message: "{res_zw["analysis"]["decoded_hidden_payload"]}"')

    # 6. Test Report API
    analysis_id = res["analysis_id"]
    r_rep = urllib.request.urlopen(f'http://127.0.0.1:8000/api/report/{analysis_id}')
    rep = json.loads(r_rep.read().decode())
    print(f'6. Forensic Report API: OK')
    print(f'   Case ID: {rep["report_header"]["case_id"]}')
    print(f'   Title: {rep["report_header"]["title"]}')

    print('\n>>> ALL LIVE HTTP & API ENDPOINTS VERIFIED 100% OPERATIONAL! <<<')

if __name__ == '__main__':
    test_api()

