<script>
(async () => {
  if (document.fonts) await document.fonts.ready;
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const svg = document.querySelector('svg'), view = svg.viewBox.baseVal;
  const box = e => { const b=e.getBBox(); return {x:b.x,y:b.y,width:b.width,height:b.height}; };
  const inside = (a,b) => a.x>=b.x-.1 && a.y>=b.y-.1 && a.x+a.width<=b.x+b.width+.1 && a.y+a.height<=b.y+b.height+.1;
  const overlaps = (a,b) => Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>.1 && Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>.1;
  const nodes = Array.from(document.querySelectorAll('.ast-node')).map(g=>({id:g.id,label:g.querySelector('text').textContent,text:box(g.querySelector('text')),rect:box(g.querySelector('rect'))}));
  const fields = Array.from(document.querySelectorAll('.edge-label')).map((e,i)=>({id:'field-'+i,label:e.textContent,text:box(e)}));
  const overflow = nodes.filter(n=>!inside(n.text,n.rect));
  const outside = [...nodes,...fields].filter(n=>!inside(n.text,view));
  const pairs = a=>a.flatMap((n,i)=>a.slice(i+1).filter(m=>overlaps(n.text,m.text)).map(m=>[n.id,m.id]));
  const data={userAgent:navigator.userAgent,font:getComputedStyle(document.querySelector('.ast-node text')).font,viewBox:{x:view.x,y:view.y,width:view.width,height:view.height},layout:svg.dataset.layout,nodeCount:nodes.length,fieldCount:fields.length,overflow:overflow.map(n=>n.id),outside:outside.map(n=>n.id),nodeOverlaps:pairs(nodes),fieldOverlaps:pairs(fields),nodes,fields};
  const p=document.createElement('pre'); p.style='white-space:pre-wrap;overflow-wrap:anywhere;font:12px monospace';
  p.textContent='MEASUREMENT '+JSON.stringify({...data,nodes:undefined,fields:undefined}); document.body.prepend(p);
  for (const n of [...nodes,...fields]) { const line=document.createElement('p'); line.textContent=JSON.stringify(n); p.after(line); }
})();
</script>
