#!/usr/bin/env python3
from pathlib import Path
import os, sys, subprocess, time, socket, urllib.request
from urllib.error import URLError
ROOT=Path(__file__).resolve().parents[1]

def choose_free_port():
  for candidate in range(18888, 19000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
      try:
        probe.bind(('127.0.0.1', candidate))
        return candidate
      except OSError:
        pass
  raise RuntimeError('no free port in 18888..18999')

def wait_for_app(base):
  deadline=time.monotonic()+10; last=None
  while time.monotonic() < deadline:
    try:
      with urllib.request.urlopen(base+'/app.js', timeout=0.5) as response:
        body=response.read().decode()
      if response.status == 200 and 'client_site_alpha' in body:
        return body
    except (URLError, OSError, TimeoutError) as exc:
      last=exc
    time.sleep(0.1)
  raise RuntimeError('API readiness failed '+repr(last))

def chrome():
  for p in [os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE'),'/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser']:
    if p and Path(p).exists(): return p
  raise SystemExit('No chrome/chromium executable found')

from playwright.sync_api import sync_playwright, expect
port=choose_free_port(); env=os.environ.copy(); env['PORT']=str(port)
proc=subprocess.Popen([sys.executable,str(ROOT/'api_server.py')],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
base=f'http://127.0.0.1:{port}'
try:
  wait_for_app(base)
  with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=chrome(), headless=True, args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.goto(base+'/', wait_until='domcontentloaded')
    expect(page.locator('text=UNDERGROUND Workbench MARKET / CLIENT FIELD').first).to_be_visible()
    expect(page.locator('text=Client Alpha')).to_be_visible()
    page.locator('text=Client Beta').click()
    expect(page.locator('text=EPSG:32633')).to_be_visible(timeout=10000)
    page.locator('[data-cell-id="L2-R6-C9"]').click(force=True)
    expect(page.locator('#gl3d')).to_have_attribute('data-selected-cell','L2-R6-C9')
    page.locator('text=Run baseline + calibration').click()
    expect(page.locator('text=Improvement')).to_be_visible(timeout=40000)
    expect(page.locator('text=Engineering Report')).to_be_visible()
    browser.close()
finally:
  proc.terminate()
  try: proc.wait(timeout=5)
  except subprocess.TimeoutExpired: proc.kill(); proc.wait()
