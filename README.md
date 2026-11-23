# 润泽说 道可道之大学

《大学》通释读本，全本十一章（v1.0.1，2026-11-23）：经一章（J01）、传十章（Z01–Z10）。一章一页，每章十二节，章末附「少年读」一段；卷首冠序一篇。

- 底本：朱熹《四书章句集注·大学章句》；参校《礼记正义·大学》郑玄注、孔颖达疏。
- 站点：<https://q1z2q3-debug.github.io/daokedao-daxue/>（Pages 走 `main:/docs`）。
- 体例：见 [`book/体例.md`](book/体例.md)；章表见 [`book/章表.md`](book/章表.md) 与 [`book/chapters.json`](book/chapters.json)。
- 底本核字：`data/底本/大学章句·经传原文.md`；校勘底账：`data/底本/校勘底账.md`。

## 结构

```
book/      一章一文件（md，唯一内容源）、序言、体例、章表、前言、附录
assets/fig 义理图源（手写 SVG，一图一文件）
scripts/   build_site.py（md → docs）、daokedao_book.py（封面扉页）
data/底本/  经传原文与校勘底账
docs/      构建产物（Pages 根）
```

## 构建

```bash
python3 scripts/build_site.py
```

## 硬约束

- 四层分离：`【经】` 原文／`【注】` 注疏／`【义】` 义理／`【用】` 今用，一段只归一层。
- 传五章为朱子补传，古本无此章；标题、正文首段、脚注、附录四处标注。
- 单文件自包含：CSS 内联、零外链脚本；义理图内嵌并另存 `docs/fig/*.svg` 供直链。
- 版本六处同号：`VERSION`、`CHANGELOG.md`、`README.md`、章节 front matter、站点页脚、章节页页脚。

## 许可

正文 CC BY-NC-SA 4.0；引文版权归原书。见 `LICENSE`。
