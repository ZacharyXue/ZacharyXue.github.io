#!/usr/bin/env python3
"""移动端适配体检：CDP 驱动 headless chrome，真实手机视口下断言横向溢出。

检查项：
  1. 页面级横向溢出（documentElement.scrollWidth > clientWidth）
  2. 溢出元素定位（article 内谁在撑宽）
  3. 表格是否被 .table-scroll 包裹（否则窄屏溢出且无法滚动）
  4. 代码块是否被 .code-scroll 包裹 + white-space 是否被改回 pre
  5. 关键正文字号（< 13px 算偏小）
  6. 可点击元素触摸目标（胶囊/链接高度 < 32px 提示）

用法: python3 mobile_check.py <base_url> <path> [path...]
"""
import asyncio
import glob
import json
import subprocess
import sys
import time
import urllib.request

import websockets

CANDIDATES = [
    '/root/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell',
    '/root/.trash-slim/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell',
]
CH = None
for pat in CANDIDATES:
    hits = glob.glob(pat)
    if hits:
        CH = hits[0]
        break
if not CH:
    sys.exit("找不到 chrome-headless-shell")

PORT = 9444
W, H = 390, 844  # iPhone 14 视口


class CDP:
    _id = 0

    def __init__(self, ws):
        self.ws = ws

    async def send(self, method, **params):
        CDP._id += 1
        mid = CDP._id
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    async def js(self, expr):
        r = await self.send(
            "Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True
        )
        return r.get("result", {}).get("value")


def start_chrome():
    proc = subprocess.Popen(
        [CH, '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
         f'--remote-debugging-port={PORT}', 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/list') as r:
                tabs = json.load(r)
            for t in tabs:
                if t.get('type') == 'page':
                    return proc, t['webSocketDebuggerUrl']
        except Exception:
            pass
        time.sleep(0.1)
    proc.kill()
    sys.exit("chrome 启动失败")


CHECK_JS = r"""
(() => {
  const de = document.documentElement;
  const out = {
    pageOverflow: de.scrollWidth - de.clientWidth,
    viewport: de.clientWidth,
    scrollWidth: de.scrollWidth,
    wideElements: [],
    tables: { total: 0, wrapped: 0 },
    codes: { total: 0, wrapped: 0, prewrap: 0 },
    bodyFont: null,
    smallTouch: 0,
  };

  // 1) 谁撑宽了页面
  document.querySelectorAll('article *, main *, body > div *').forEach(el => {
    const sw = el.scrollWidth, cw = el.clientWidth;
    const rect = el.getBoundingClientRect();
    if (rect.width > 0 && (rect.right > de.clientWidth + 1 || sw > cw + 2)) {
      if (out.wideElements.length < 8) {
        out.wideElements.push({
          tag: el.tagName.toLowerCase(),
          cls: (el.className || '').toString().slice(0, 40),
          rectW: Math.round(rect.width),
          right: Math.round(rect.right),
          sw, cw,
        });
      }
    }
  });

  // 2) 表格包裹
  document.querySelectorAll('article table').forEach(t => {
    out.tables.total++;
    if (t.parentElement && t.parentElement.classList.contains('table-scroll')) out.tables.wrapped++;
  });

  // 3) 代码块包裹 + white-space
  document.querySelectorAll('article pre').forEach(p => {
    out.codes.total++;
    if (p.parentElement && p.parentElement.classList.contains('code-scroll')) out.codes.wrapped++;
    const ws = getComputedStyle(p).whiteSpace;
    if (ws !== 'pre') out.codes.prewrap++;
  });

  // 4) 正文字号
  const p = document.querySelector('article p, main p');
  if (p) out.bodyFont = getComputedStyle(p).fontSize;

  // 5) 触摸目标：chip / tag / 主要链接高度 < 32px
  document.querySelectorAll('.chip, .rw-chip, .card-foot .tag, .wiki-tags .tag, .pager-item').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.height > 0 && r.height < 32) out.smallTouch++;
  });

  return JSON.stringify(out);
})()
"""


async def main():
    base = sys.argv[1].rstrip('/')
    paths = sys.argv[2:]
    proc, ws_url = start_chrome()
    try:
        async with websockets.connect(ws_url, max_size=40_000_000) as ws:
            c = CDP(ws)
            await c.send('Page.enable')
            await c.send('Runtime.enable')
            await c.send('Emulation.setDeviceMetricsOverride',
                         width=W, height=H, deviceScaleFactor=2, mobile=True)
            await c.send('Emulation.setTouchEmulationEnabled', enabled=True)

            for path in paths:
                await c.send('Page.navigate', url=base + path)
                await asyncio.sleep(1.6)
                raw = await c.js(CHECK_JS)
                if not raw:
                    print(f"\n=== {path} ===\n  ❌ 取不到数据")
                    continue
                d = json.loads(raw)
                flags = []
                if d['pageOverflow'] > 1:
                    flags.append(f"页面横向溢出 {d['pageOverflow']}px")
                if d['tables']['total'] and d['tables']['wrapped'] < d['tables']['total']:
                    flags.append(f"表格 {d['tables']['total']-d['tables']['wrapped']}/{d['tables']['total']} 未包滚动容器")
                if d['codes']['total'] and d['codes']['wrapped'] < d['codes']['total']:
                    flags.append(f"代码块 {d['codes']['total']-d['codes']['wrapped']}/{d['codes']['total']} 未包滚动容器")
                if d['codes']['prewrap']:
                    flags.append(f"代码块 {d['codes']['prewrap']} 个仍是 pre-wrap（会被软折行）")
                if d['smallTouch']:
                    flags.append(f"{d['smallTouch']} 个可点元素高度 <32px")
                status = '✅' if not flags else '❌'
                print(f"\n{status} {path}  (viewport {d['viewport']} / scrollW {d['scrollWidth']})")
                if d['tables']['total']:
                    print(f"   表格 {d['tables']['wrapped']}/{d['tables']['total']} 已包裹")
                if d['codes']['total']:
                    print(f"   代码块 {d['codes']['wrapped']}/{d['codes']['total']} 已包裹, pre-wrap {d['codes']['prewrap']}")
                print(f"   正文字号 {d['bodyFont']}")
                for f in flags:
                    print(f"   ⚠️  {f}")
                if d['pageOverflow'] > 1 and d['wideElements']:
                    print("   撑宽元素:")
                    for e in d['wideElements'][:5]:
                        print(f"     <{e['tag']} class='{e['cls']}'> w={e['rectW']} right={e['right']} sw/cw={e['sw']}/{e['cw']}")
    finally:
        proc.kill()


if __name__ == '__main__':
    asyncio.run(main())
