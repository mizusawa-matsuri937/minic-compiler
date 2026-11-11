// AC24 浏览器实测脚本（评审者 Claude，2026-11-11）。
// 用法：在 1280 像素宽的视口中打开 ast.html，在页面上下文中整段执行，取最后一个表达式的值。
// 脚本只读页面并点击页面自带的两个按钮，不改写页面内容。
await document.fonts.ready;
await new Promise(resolve => setTimeout(resolve, 300));

const measure = () => {
  const container = document.getElementById('ast-tree');
  const svg = container.querySelector('svg');
  const root = svg.querySelector('.ast-node rect').getBoundingClientRect();
  const box = container.getBoundingClientRect();
  const nodes = [...svg.querySelectorAll('.ast-node rect')].map(e => e.getBoundingClientRect());
  // 可视区域 = 容器去掉边框后的内容区
  const visL = box.left + container.clientLeft, visR = visL + container.clientWidth;
  return {
    inner: [innerWidth, innerHeight],
    container: {left: box.left, right: box.right, top: box.top, bottom: box.bottom, visL, visR,
                clientWidth: container.clientWidth, scrollWidth: container.scrollWidth,
                scrollLeft: container.scrollLeft},
    root: {left: root.left, right: root.right, top: root.top, bottom: root.bottom,
           label: svg.querySelector('.ast-node text').textContent},
    rootInView: root.left >= visL && root.right <= visR && root.top >= 0 && root.bottom <= innerHeight,
    centerErr: (root.left + root.right) / 2 - (visL + visR) / 2,
    svg: {width: svg.getAttribute('width'), height: svg.getAttribute('height'),
          viewBox: svg.getAttribute('viewBox'), layout: svg.dataset.layout},
    nodes: nodes.length,
    minLeft: Math.min(...nodes.map(n => n.left)),
    maxRight: Math.max(...nodes.map(n => n.right)),
    allInWidth: nodes.every(n => n.left >= visL && n.right <= visR),
    pressed: [document.getElementById('ast-fit').getAttribute('aria-pressed'),
              document.getElementById('ast-actual').getAttribute('aria-pressed')],
    pageScrollWidth: document.documentElement.scrollWidth,
  };
};

const out = {ua: navigator.userAgent, initial: measure()};
document.getElementById('ast-fit').click();
out.fit = measure();
document.getElementById('ast-actual').click();
out.actual = measure();
JSON.stringify(out);
