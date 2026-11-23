#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《大学》全书自检：体例、字数、脚注、四层标记、图、版本、章表一致性。

用法：python3 scripts/check_book.py [--strict]
退出码：0 全过；1 有 FAIL。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
DOCS = os.path.join(ROOT, "docs")
FIG = os.path.join(ROOT, "assets", "fig")
VERSION = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
CFG = json.load(open(os.path.join(BOOK, "chapters.json"), encoding="utf-8"))
CH = CFG["chapters"]

SECTIONS = ["本章导读", "经文", "字义与句读", "今译", "章旨", "朱子注",
            "分寸与边界", "义理", "时代之问", "跨典", "存疑", "双卡与图"]
COLORS = {"#F7F4EE", "#25211D", "#994433", "#7C6D5C", "#DCD5C8", "#FCFAF6"}

fails, warns = [], []


def fail(m):
    fails.append(m)


def warn(m):
    warns.append(m)


def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def strip_fm(t):
    if t.startswith("---"):
        e = t.find("\n---", 3)
        if e > 0:
            return t[e + 4:]
    return t


def body_chars(md):
    t = strip_fm(md)
    # 去掉章末少年读、附论与脚注定义
    t = re.split(r"\n## 少年读", t)[0]
    t = re.sub(r"(?m)^\[\^[0-9]+\]:.*$", "", t)
    return cjk(t)


def load_base():
    """底本各章原文，去标点，仅汉字。"""
    t = open(os.path.join(ROOT, "data", "底本", "大学章句·经传原文.md"), encoding="utf-8").read()
    out = {}
    for p in re.split(r"\n## ", t)[1:]:
        head = p.split("\n")[0]
        body = "\n".join(p.split("\n")[1:])
        body = re.sub(r"〔.*?〕", "", body, flags=re.S)
        out[head.split("　")[0].split("（")[0]] = re.sub(r"[^\u4e00-\u9fff]", "", body)
    return out


BASE = None


def check_text(ch):
    global BASE
    if BASE is None:
        BASE = load_base()
    key = ch["id"].replace("J", "经").replace("Z", "传")
    key = {"J01": "经一章"}.get(ch["id"], "传" + "一二三四五六七八九十"[int(ch["id"][1:]) - 1] + "章")
    base = BASE.get(key)
    if not base:
        fail("%s 底本找不到 %s" % (ch["id"], key))
        return
    md = open(os.path.join(ROOT, ch["file"]), encoding="utf-8").read()
    sec = re.split(r"## 二　经文", md)[1].split("## 三　")[0]
    quoted = "".join(re.findall(r"【经】\s*(.+)", sec))
    quoted = re.sub(r"\[\^[0-9]+\]", "", quoted)
    q = re.sub(r"[^\u4e00-\u9fff]", "", quoted)
    if q not in base:
        # 找出第一处不一致
        for i in range(min(len(q), len(base))):
            if q[i] != base[i]:
                fail("%s 经文与底本不符：第 %d 字 %s ≠ %s（…%s…）"
                     % (ch["id"], i + 1, q[i], base[i], q[max(0, i - 8):i + 8]))
                return
        fail("%s 经文长度与底本不符：%d vs %d" % (ch["id"], len(q), len(base)))


def check_chapter(ch):
    path = os.path.join(ROOT, ch["file"])
    if not os.path.exists(path):
        fail("%s 缺文件 %s" % (ch["id"], ch["file"]))
        return
    md = open(path, encoding="utf-8").read()
    fm = md.split("---")[1] if md.startswith("---") else ""
    if "version: %s" % VERSION not in fm:
        fail("%s front matter version 不是 %s" % (ch["id"], VERSION))
    if ("id: %s" % ch["id"]) not in fm:
        fail("%s front matter id 不符" % ch["id"])

    heads = re.findall(r"(?m)^##\s+(.+)$", md)
    names = [re.sub(r"^[一二三四五六七八九十]+　", "", h).strip() for h in heads]
    core = [n for n in names if n in SECTIONS]
    if core != SECTIONS:
        fail("%s 十二节顺序/名称不符：%s" % (ch["id"], "、".join(core)))
    extra_ok = all((n in SECTIONS or n == "少年读" or n.startswith("附论")) for n in names)
    if not extra_ok:
        fail("%s 有多余节：%s" % (ch["id"], [n for n in names if not (n in SECTIONS or n == "少年读" or n.startswith("附论"))]))

    check_text(ch)

    n = body_chars(md)
    if not (3000 <= n <= 6000):
        fail("%s 正文 %d 字，不在 3000–6000" % (ch["id"], n))

    defined = re.findall(r"(?m)^\[\^([0-9]+)\]:", md)
    used = set(re.findall(r"\[\^([0-9]+)\](?!:)", md))
    if len(defined) < 5:
        fail("%s 脚注定义 %d 条 < 5" % (ch["id"], len(defined)))
    unused = [d for d in defined if d not in used]
    if unused:
        fail("%s 脚注被定义未引用：%s（pandoc 会丢弃）" % (ch["id"], unused))

    if md.count("【义】") + md.count("【用】") < 8:
        fail("%s 【义】+【用】不足 8 段" % ch["id"])
    if "【经】" not in md:
        fail("%s 无【经】原文标记" % ch["id"])
    if md.count("- ") and not re.search(r"- .+→.+\n", md):
        warn("%s 双卡格式可能不符" % ch["id"])
    dui = len(re.findall(r"(?m)^-\s+.+→.+$", md))
    if dui < 4:
        fail("%s 双卡 %d 对 < 4" % (ch["id"], dui))

    if not re.search(r"## 少年读", md):
        fail("%s 缺少年读" % ch["id"])
    else:
        sw = re.split(r"## 少年读", md)[1].split("## 附论")[0]
        m1 = re.search(r"一件事", sw)
        q = len(re.findall(r"(?m)^\d\.\s", sw))
        if not m1 or q != 3:
            fail("%s 少年读缺「一件事」或三个问题（%d）" % (ch["id"], q))
        body = sw.split("**一件事")[0]
        sc = cjk(re.sub(r"\*\*[^*]+\*\*", "", body))
        if not (100 <= sc <= 260):
            warn("%s 少年读约 %d 字（100–200 为宜）" % (ch["id"], sc))

    svg = os.path.join(FIG, ch["id"].lower() + ".svg")
    if not os.path.exists(svg):
        fail("%s 缺义理图 %s" % (ch["id"], svg))
    else:
        s = open(svg, encoding="utf-8").read()
        if "<title>" not in s or "<desc>" not in s:
            fail("%s 图缺 title/desc" % ch["id"])
        if "viewBox" not in s:
            fail("%s 图缺 viewBox" % ch["id"])
        if re.search(r'<svg[^>]*(width|height)="[0-9]', s):
            fail("%s 图写了固定 width/height" % ch["id"])
        used_colors = set(re.findall(r"#[0-9A-Fa-f]{6}", s))
        bad = used_colors - COLORS
        if bad:
            fail("%s 图用非规定色：%s" % (ch["id"], bad))
        small = [int(x) for x in re.findall(r'font-size="([0-9]+)"', s) if int(x) < 11]
        if small:
            fail("%s 图字号 <11：%s" % (ch["id"], small))
        if "<text" not in s:
            fail("%s 图无 text" % ch["id"])


def check_version():
    for f, pat in (("README.md", r"v?%s" % re.escape(VERSION)),
                   ("CHANGELOG.md", r"## %s" % re.escape(VERSION)),
                   ("CITATION.cff", r"version: %s" % re.escape(VERSION))):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            fail("缺 %s" % f)
        elif not re.search(pat, open(p, encoding="utf-8").read()):
            fail("%s 未写版本 %s" % (f, VERSION))


def check_toc():
    p = os.path.join(BOOK, "章表.md")
    t = open(p, encoding="utf-8").read()
    for ch in CH:
        if ch["id"] not in t or ch["file"] not in t:
            fail("章表.md 与 chapters.json 不一致：%s" % ch["id"])


def check_z05():
    p = os.path.join(BOOK, "Z05-释格物致知.md")
    if not os.path.exists(p):
        fail("缺 Z05")
        return
    t = open(p, encoding="utf-8").read()
    if not re.search(r"(?m)^# .*（朱子补传", t):
        fail("Z05 标题未标补传")
    first = re.split(r"## 二　经文", t)[1][:400] if "## 二　经文" in t else ""
    if "朱子补传" not in first or "古本" not in first:
        fail("Z05 正文首段未标补传／古本")
    if not re.search(r"(?m)^\[\^[0-9]+\]:.*朱子补传", t):
        fail("Z05 脚注未标补传")
    ap = []
    for f in ("book/附录-01-古本全文.md", "book/附录-02-对照表.md"):
        q = os.path.join(ROOT, f)
        if os.path.exists(q):
            ap.append(open(q, encoding="utf-8").read())
    if len(ap) < 2:
        fail("附录页缺失，第四处补传标注未落实")
    elif not all("古本无此章" in x for x in ap):
        fail("附录未标「古本无此章」（第四处）")


def check_site():
    for p in ("index.html", "book.html", "sitemap.xml", "robots.txt", "llms.txt", "404.html", "favicon.svg"):
        if not os.path.exists(os.path.join(DOCS, p)):
            fail("站点缺 %s" % p)
    for ch in CH:
        if not os.path.exists(os.path.join(DOCS, ch["page"])):
            fail("站点缺章页 %s" % ch["page"])
    idx = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
    if idx.count("href=\"ch/") < len(CH):
        fail("首页目录链不足 11 条")
    for ch in CH:
        pp = os.path.join(DOCS, ch["page"])
        if not os.path.exists(pp):
            continue
        page = open(pp, encoding="utf-8").read()
        if "../%s" % ch["fig"] not in page:
            fail("%s 页缺 SVG 直链" % ch["id"])
        if VERSION not in page:
            fail("%s 页脚版本不符" % ch["id"])


def main():
    for ch in CH:
        check_chapter(ch)
    check_version()
    check_toc()
    check_z05()
    check_site()
    print(json.dumps({"version": VERSION, "chapters": len(CH),
                      "FAIL": fails, "WARN": warns}, ensure_ascii=False, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
