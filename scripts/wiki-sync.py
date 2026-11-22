#!/usr/bin/env python3
"""
wiki-sync — /root/wiki（加密源）→ 博客站 src/content/wiki/（公开明文）

设计约束：
  1. 单向：源永远只有 /root/wiki，本站目录是生成物，手改会被覆盖
  2. **默认私有**：wiki 是加密私有仓，默认不出网。只有下面两种显式放行才发布：
       - 目录白名单 PUBLIC_DIRS（整个目录默认公开）
       - 页级 frontmatter `visibility: public`（白名单外单页放行）
     页级 `visibility: private` 优先级最高，可阻断白名单内的例外页
  3. 敏感词兜底：命中 DENY 规则的页拒发并列报告，不静默通过
  4. wikilink：[[basename|中文]] → [中文](/wiki/<domain>/<slug>)，死链降级成纯文本并警告

⚠️ 安全默认是「不发布」。新增 wiki 页默认躺平在私有侧，要公开必须主动放行——
   这正是「私有仓不该默认漏内容」的正确方向，别改回去。

用法：
  python3 scripts/wiki-sync.py --dry-run   # 只出报告，不写盘（首次必跑）
  python3 scripts/wiki-sync.py             # 真同步
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

WIKI = Path("/root/wiki")
BLOG = Path("/root/ZacharyXue.github.io")
DEST = BLOG / "src" / "content" / "wiki"
INDEX_JSON = BLOG / "src" / "data" / "wiki-index.json"
LINKS_JSON = BLOG / "src" / "data" / "wiki-links.json"
BLOG_DIR = BLOG / "src" / "content" / "blog"
BLOG_URL_RE = re.compile(r"https?://zacharyxue\.github\.io/blog/([\w\-]+)/?")
BLOG_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")

# 域目录 → 展示名（顺序即站点索引页分区顺序）
# 域配置：(站点 domain id, 源相对路径, 展示名)
# domain id 直接决定 URL：/wiki/<id>/<slug>
DOMAIN_SPECS = [
    ("investing",    "concepts/investing",    "投资认知"),
    ("cloud-native", "concepts/cloud-native", "云原生"),
    ("llm-eng",      "concepts/llm-eng",      "LLM 工程"),
    ("algorithms",   "concepts/algorithms",   "算法范式"),
    ("soft-skills",  "concepts/soft-skills",  "读书软技能"),
    ("stocks",       "entities/investing",    "个股与指数"),
    ("systems",      "entities/systems",      "个人系统"),
]
DOMAINS = {d: label for d, _, label in DOMAIN_SPECS}

# 目录级公开白名单：只有这些目录下的页默认公开。
# 不在白名单 = 默认私有（新目录/新实体页不会自动出网）。
PUBLIC_DIRS = {
    "concepts/investing",
    "concepts/cloud-native",
    "concepts/llm-eng",
    "concepts/algorithms",
    "concepts/soft-skills",  # 读书软技能：用户确认可以公开（2026-11-22）
    "entities/investing",   # 个股/指数/基金 → 公开
    # entities/systems 故意不在白名单：简历/看板/技能库/内网代理等个人系统默认私有
}

# 拒绝级：命中即不进公开站（个人路径 / 薪酬 / 持仓成本）
DENY = [
    (r"zach-skills", "技能库内部路径"),
    (r"\.hermes", "Hermes 内部路径"),
    (r"career-data", "职业数据路径"),
    (r"social-data", "社交数据路径"),
    (r"总包", "个人薪酬"),
    (r"薪资", "个人薪酬"),
    (r"成本价", "持仓成本"),
    (r"我的持仓", "个人持仓"),
    (r"我持有", "个人持仓"),
    (r"我买入", "个人交易"),
]

# 警告级：不拦，但报告里点名，人工过一眼
WARN = [
    (r"10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+", "内网/私网地址"),
    (r"阿里云|腾讯云|华为云", "云厂商环境"),
    (r"公司内网|内部域名|内网域名|\bcorp\b", "内部系统措辞"),
]


# ---------------------------------------------------------------- frontmatter

def split_fm(text: str) -> tuple[dict, str]:
    """返回 (frontmatter 字典, 正文)。只处理平铺 key: value + 简单列表。"""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw, body = parts[1], parts[2]
    fm: dict = {}
    cur_list_key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s+-\s+", line) and cur_list_key:
            fm[cur_list_key].append(line.strip()[1:].strip())
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
        elif val == "":
            fm[key] = []
            cur_list_key = key
        else:
            fm[key] = val.strip('"').strip("'")
            cur_list_key = None
    return fm, body


def strip_leading_h1(body: str) -> str:
    """正文开头的 `# 标题` 与 frontmatter title 重复，去掉（layout 统一渲染 h1）。"""
    return re.sub(r"^\s*#\s+[^\n]+\n+", "", body, count=1)


def extract_essence(body: str, fm: dict) -> str | None:
    """从「## 一句话本质 / 一句话本质」段抓第一段实质文字做卡片摘要。"""
    m = re.search(r"^#+\s*一句话本质[^\n]*\n+(.+?)(?:\n\s*\n|\n#|\Z)", body, re.M | re.S)
    if m:
        s = m.group(1).strip()
        s = re.sub(r"\*\*|`|\[|\]|\(|\)", "", s)
        s = re.sub(r"\s+", " ", s)
        return s[:180] + ("…" if len(s) > 180 else "")
    # 兜底：正文第一段
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if para and not para.startswith("#") and not para.startswith(">"):
            para = re.sub(r"\*\*|`|\[|\]|\(|\)", "", para)
            para = re.sub(r"\s+", " ", para)
            return para[:180] + ("…" if len(para) > 180 else "")
    return None


# ---------------------------------------------------------------- 收集 & 筛选

def load_blog_titles() -> dict[str, str]:
    """博客 slug → 标题。slug 规则与 blog/[slug].astro 一致（去掉日期前缀）。"""
    titles: dict[str, str] = {}
    if not BLOG_DIR.exists():
        return titles
    for f in BLOG_DIR.glob("*.md"):
        fm, _body = split_fm(f.read_text(encoding="utf-8"))
        slug = BLOG_DATE_PREFIX_RE.sub("", f.stem)
        titles[slug] = str(fm.get("title", slug))
    return titles


def collect() -> list[dict]:
    pages = []
    for domain, relpath, _label in DOMAIN_SPECS:
        d = WIKI / relpath
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            fm, body = split_fm(text)
            pages.append({
                "domain": domain,
                "slug": f.stem,
                "dirpath": relpath,
                "path": f,
                "fm": fm,
                "body": body,
                "text": text,
            })
    return pages


def scan(text: str, patterns) -> list[str]:
    hits = []
    for pat, label in patterns:
        if re.search(pat, text):
            hits.append(label)
    return hits


# ---------------------------------------------------------------- wikilink

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
# 围栏代码块：里面的 [[...]] 是 TOML 数组表语法（如 [[worker.oci.gcpolicy]]），
# 不是 wikilink，转换和出链统计都必须跳过，否则会误判成死链
FENCE_RE = re.compile(r"(```.*?```)", re.S)


def iter_prose(body: str):
    """按围栏代码块切分，产出 (is_code, chunk)。"""
    for i, part in enumerate(FENCE_RE.split(body)):
        if not part:
            continue
        yield (i % 2 == 1, part)


def convert_wikilinks(body: str, linkmap: dict[str, tuple[str, str]], warn: list[str], slug: str) -> str:
    """[[slug|中文]] → [中文](/wiki/domain/slug)；死链降级为纯文本；代码块原样保留。"""
    out: list[str] = []
    for is_code, chunk in iter_prose(body):
        if is_code:
            out.append(chunk)
            continue

        def repl(m: re.Match) -> str:
            target = m.group(1).strip()
            label = (m.group(2) or "").strip() or target
            key = target.replace(".md", "")
            if key in linkmap:
                domain, s = linkmap[key]
                return f"[{label}](/wiki/{domain}/{s})"
            warn.append(f"{slug}: 死链 [[{target}]] 已降级为纯文本")
            return label

        out.append(WIKILINK_RE.sub(repl, chunk))
    return "".join(out)


# ---------------------------------------------------------------- 主流程

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只出报告不写盘")
    args = ap.parse_args()

    pages = collect()
    if not pages:
        print("❌ 未在 /root/wiki 找到任何页，检查源路径", file=sys.stderr)
        return 1

    published, skipped, denied, warns = [], [], [], []

    for p in pages:
        # 判定顺序：页级 private > 页级 public > 目录白名单 > 默认私有
        vis = str(p["fm"].get("visibility", "")).lower()
        if vis == "private":
            skipped.append((p, "页级 visibility: private"))
            continue
        if vis == "public":
            p["publish_reason"] = "页级 visibility: public"
        elif p["dirpath"] in PUBLIC_DIRS:
            p["publish_reason"] = f"目录白名单 {p['dirpath']}/"
        else:
            skipped.append((p, "默认私有（目录不在白名单，且无页级 visibility: public）"))
            continue
        deny_hits = scan(p["text"], DENY)
        if deny_hits:
            denied.append((p, deny_hits))
            continue
        warns.extend(f"{p['slug']}: {w}" for w in scan(p["text"], WARN))
        published.append(p)

    # ---- 报告
    print("=" * 62)
    print(f"源页共 {len(pages)}  |  发布 {len(published)}  |  默认私有跳过 {len(skipped)}  |  敏感词拦下 {len(denied)}")
    print("=" * 62)
    if skipped:
        print("\n🔒 不发布（私有侧）：")
        for p, why in skipped:
            print(f"   - {p['domain']}/{p['slug']}  ({why})")
    if denied:
        print("\n⛔ 敏感词拦下（需人工处理后重跑）：")
        for p, hits in denied:
            print(f"   - {p['domain']}/{p['slug']}  ← {', '.join(hits)}")
    if warns:
        print(f"\n⚠️  警告 {len(warns)} 条（不拦，人工过一眼）：")
        for w in warns[:15]:
            print(f"   - {w}")
        if len(warns) > 15:
            print(f"   ... 另 {len(warns)-15} 条")

    print(f"\n📊 发布清单（按域）：")
    by_domain: dict[str, list] = {}
    for p in published:
        by_domain.setdefault(p["domain"], []).append(p)
    for d, label in DOMAINS.items():
        items = by_domain.get(d, [])
        if items:
            reasons = {p.get("publish_reason", "?") for p in items}
            why = reasons.pop() if len(reasons) == 1 else "混合放行"
            print(f"   {label:12s} {len(items):2d} 页  ← {why}")

    if args.dry_run:
        print("\n[dry-run] 未写盘。确认无误后去掉 --dry-run 重跑。")
        return 0

    # ---- 写盘
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)

    # slug → (domain, slug) 映射，**只含已发布页**：
    # 指向私有页的 wikilink 必须降级为纯文本，否则会生成站内死链。
    linkmap = {p["slug"]: (p["domain"], p["slug"]) for p in published}

    index_data = []
    outlinks: dict[str, list[str]] = {}   # wiki key -> [目标 wiki key]
    wiki_meta: dict[str, dict] = {}       # wiki key -> 元信息
    for p in published:
        key = f"{p['domain']}/{p['slug']}"
        # 出链（基于转换前的原始 wikilink，用于算入链；跳过代码块里的 TOML 语法）
        targets: list[str] = []
        for is_code, chunk in iter_prose(p["body"]):
            if is_code:
                continue
            for m in WIKILINK_RE.finditer(chunk):
                t = m.group(1).strip().replace(".md", "")
                if t in linkmap:
                    tk = f"{linkmap[t][0]}/{linkmap[t][1]}"
                    if tk != key and tk not in targets:
                        targets.append(tk)
        outlinks[key] = targets

        body = convert_wikilinks(p["body"], linkmap, warns, p["slug"])
        body = strip_leading_h1(body)
        essence = extract_essence(body, p["fm"])
        fm = p["fm"]
        out_fm = {
            "title": fm.get("title", p["slug"]),
            "domain": p["domain"],
            "domainLabel": DOMAINS[p["domain"]],
            "created": fm.get("created", ""),
            "updated": fm.get("updated", fm.get("created", "")),
            "type": fm.get("type", "concept"),
            "tags": fm.get("tags", []),
            "sources": fm.get("sources", []),
            "confidence": fm.get("confidence", ""),
            "summary": essence or "",
        }
        # 重建 frontmatter
        lines = ["---"]
        for k, v in out_fm.items():
            if isinstance(v, list):
                if not v:
                    lines.append(f"{k}: []")
                    continue
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
            else:
                lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        lines.append("---")
        out_path = DEST / p["domain"] / f"{p['slug']}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n" + body, encoding="utf-8")

        index_data.append({
            "domain": p["domain"],
            "domainLabel": DOMAINS[p["domain"]],
            "slug": p["slug"],
            "title": out_fm["title"],
            "summary": essence or "",
            "tags": out_fm["tags"],
            "updated": out_fm["updated"],
        })
        wiki_meta[key] = {
            "title": out_fm["title"],
            "domain": p["domain"],
            "domainLabel": DOMAINS[p["domain"]],
            "slug": p["slug"],
        }

    INDEX_JSON.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 关系计算：点↔线（sources 里的博客 URL）+ 反向链接（wikilink 入链）
    blog_titles = load_blog_titles()
    wiki_to_blog: dict[str, list[str]] = {}
    blog_to_wiki: dict[str, list[str]] = {}

    for p in published:
        key = f"{p['domain']}/{p['slug']}"
        srcs = p["fm"].get("sources", [])
        if isinstance(srcs, str):
            srcs = [srcs]
        for s in srcs:
            m = BLOG_URL_RE.search(str(s))
            if not m:
                continue
            bs = m.group(1)
            if bs not in blog_titles:      # 只认站上真实存在的博客
                warns.append(f"{p['slug']}: sources 指向不存在的博客 /blog/{bs}/")
                continue
            lst = wiki_to_blog.setdefault(key, [])
            if bs not in lst:
                lst.append(bs)
            rev = blog_to_wiki.setdefault(bs, [])
            if key not in rev:
                rev.append(key)

    backlinks: dict[str, list[str]] = {}
    for src, tgts in outlinks.items():
        for t in tgts:
            if t in wiki_meta:
                rev = backlinks.setdefault(t, [])
                if src not in rev:
                    rev.append(src)

    def wref(k: str) -> dict:
        m = wiki_meta[k]
        return {
            "key": k,
            "title": m["title"],
            "domain": m["domain"],
            "domainLabel": m["domainLabel"],
            "slug": m["slug"],
            "href": f"/wiki/{m['domain']}/{m['slug']}",
        }

    links_data = {
        "blogToWiki": {
            bs: [wref(k) for k in ks if k in wiki_meta]
            for bs, ks in blog_to_wiki.items()
        },
        "wikiToBlog": {
            k: [
                {"slug": bs, "title": blog_titles[bs], "href": f"/blog/{bs}"}
                for bs in bss
            ]
            for k, bss in wiki_to_blog.items()
        },
        "wikiBacklinks": {
            k: [wref(s) for s in ss if s in wiki_meta]
            for k, ss in backlinks.items()
        },
    }
    LINKS_JSON.write_text(json.dumps(links_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 已写入 {len(published)} 页 → {DEST.relative_to(BLOG)}")
    print(f"✅ 索引 → {INDEX_JSON.relative_to(BLOG)}")
    print(f"✅ 关系 → {LINKS_JSON.relative_to(BLOG)}")
    print(f"   点↔线：{len(wiki_to_blog)} 个知识点挂了长文出处，{len(blog_to_wiki)} 篇博客挂了知识点")
    print(f"   反链：{len(backlinks)} 个知识点被引用（共 {sum(len(v) for v in backlinks.values())} 条入链）")
    if warns:
        # wikilink 死链在转换阶段才产生（指向私有页或被删页），单独列出来，别埋在内容警告里
        deadlinks = [w for w in warns if "死链" in w or "指向不存在" in w]
        if deadlinks:
            print(f"\n🔗 链接降级 {len(deadlinks)} 条（目标页私有/不存在，已降为纯文本）：")
            for w in deadlinks:
                print(f"   - {w}")
        others = len(warns) - len(deadlinks)
        if others:
            print(f"⚠️  另有 {others} 条内容警告（内网地址/云厂商等，见上）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
