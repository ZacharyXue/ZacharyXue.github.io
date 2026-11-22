/**
 * 文章正文增强 —— BlogLayout 与 WikiLayout 共用同一份实现。
 *
 * 为什么必须共用：手机上最刺眼的两个毛病都出在这里，
 * 一个 layout 有、另一个没有，就会一半页面正常一半页面横向溢出。
 * 改这里一处，博客页和 wiki 页同时生效；不要在某个 layout 里单独改。
 *
 * 1) 表格：Astro 侧是 display:table + width:100%，窄屏会被内容撑宽；
 *    包一层 .table-scroll（样式在 global.css，因为它是 JS 动态创建、
 *    没有 Astro scoped 属性）承担横向滚动与外框。
 * 2) 代码块：Astro 给每个 <pre> 内联了 white-space:pre-wrap + word-wrap:break-word，
 *    代码会软折行——折出来的行看起来像新语句、注释被拆断、缩进错乱，
 *    手机上尤其容易读错。包 .code-scroll 并把 white-space 改回 pre，
 *    溢出让横向滚动 + 下方「↔ 左右滑动」提示承担。
 * 3) 标题锚点：hover 显形、点击复制本节链接（桌面阅读用，移动端静息不可见）。
 */

/** 给正文里的每张表包一层横向滚动容器，返回新包裹的数量 */
export function wrapTables(root: ParentNode = document): number {
  let n = 0;
  root.querySelectorAll<HTMLTableElement>('article .article-body table').forEach(table => {
    const parent = table.parentElement;
    if (!parent || parent.classList.contains('table-scroll')) return;
    const wrap = document.createElement('div');
    wrap.className = 'table-scroll';
    parent.insertBefore(wrap, table);
    wrap.appendChild(table);

    // 手机上表格横滑是隐形的：溢出时给一行「↔ 左右滑动」提示
    const sync = () => {
      wrap.classList.toggle('is-scrollable', table.scrollWidth > wrap.clientWidth + 2);
    };
    sync();
    window.addEventListener('resize', sync);
    setTimeout(sync, 400); // 字体/布局稳定后再量一次
    n++;
  });
  return n;
}

/** 给每个代码块包滚动容器并覆盖内联 white-space，返回新包裹的数量 */
export function wrapCodeBlocks(root: ParentNode = document): number {
  let n = 0;
  root.querySelectorAll<HTMLElement>('article .article-body pre').forEach(pre => {
    // mermaid 块会被替换成图形，不包（否则留下空壳容器）
    if (pre.dataset.language === 'mermaid') return;
    if (pre.parentElement?.classList.contains('code-scroll')) return;

    const wrap = document.createElement('div');
    wrap.className = 'code-scroll';
    pre.parentNode?.insertBefore(wrap, pre);
    wrap.appendChild(pre);

    pre.style.whiteSpace = 'pre';
    pre.style.wordWrap = 'normal';
    pre.style.overflowWrap = 'normal';

    const sync = () => {
      wrap.classList.toggle('is-scrollable', pre.scrollWidth > pre.clientWidth + 2);
    };
    sync();
    window.addEventListener('resize', sync);
    setTimeout(sync, 400); // 字体/布局稳定后再量一次
    n++;
  });
  return n;
}

/** 给 h2/h3/h4 追加锚点，点击复制「本节链接」 */
export function addHeadingAnchors(root: ParentNode = document): number {
  let n = 0;
  root.querySelectorAll<HTMLElement>('article .article-body :is(h2, h3, h4)').forEach(h => {
    if (!h.id || h.querySelector('.heading-anchor')) return;
    const a = document.createElement('a');
    a.className = 'heading-anchor';
    a.href = '#' + h.id;
    a.title = '复制本节链接';
    a.setAttribute('aria-label', '复制本节链接');
    a.textContent = '#';
    a.addEventListener('click', ev => {
      const url = location.origin + location.pathname + '#' + h.id;
      if (!navigator.clipboard?.writeText) return; // 不支持就按普通锚点跳转
      ev.preventDefault();
      navigator.clipboard.writeText(url).then(() => {
        a.textContent = '✓';
        setTimeout(() => { a.textContent = '#'; }, 1200);
      }).catch(() => { location.hash = h.id; });
    });
    h.appendChild(a);
    n++;
  });
  return n;
}

/** 一次跑完三项 */
export function enhanceArticle(root: ParentNode = document): void {
  wrapTables(root);
  wrapCodeBlocks(root);
  addHeadingAnchors(root);
}
