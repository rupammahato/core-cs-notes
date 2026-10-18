const d3=window.d3;
const palette={Search:'#285c88',Social:'#ad5719'};
const definitions={spend_cents:{title:'Compare campaign spend',unit:'USD',format:v=>'$'+(v/100).toFixed(2)},
  clicks:{title:'Compare campaign clicks',unit:'clicks',format:v=>String(v)},
  reported_roas:{title:'Compare reported ROAS',unit:'times media spend',format:v=>v.toFixed(2)+'×'}};
const source=await fetch('/measurement-output.json').then(response=>{
  if(!response.ok)throw new Error('Could not load the prepared snapshot');return response.json();
});
let current=[];
function setData(rows){
  const keys=new Set();
  for(const row of rows){
    if(!row.campaign_id||keys.has(row.campaign_id)||!(row.channel in palette))throw new Error('Need unique campaign keys and known channels');
    keys.add(row.campaign_id);
    for(const value of [row.spend_cents,row.clicks,row.metrics.reported_roas])
      if(value!==null&&(!Number.isFinite(value)||value<0))throw new Error('Need known nonnegative values or explicit null');
  }
  current=structuredClone(rows);render();
}
function selected(){const channel=document.querySelector('#channel').value;return current.filter(row=>channel==='All'||row.channel===channel);}
function render(){
  const rows=selected(),metric=document.querySelector('#metric').value,def=definitions[metric];
  const value=row=>metric==='reported_roas'?row.metrics.reported_roas:row[metric];
  const valid=rows.filter(row=>value(row)!==null);
  const canvasWidth=Math.max(320,document.querySelector('#bars').clientWidth);
  const left=138,width=canvasWidth-left-70,top=30,height=190;
  d3.select('#bars').attr('viewBox',`0 0 ${canvasWidth} 270`);
  d3.select('#treemap').attr('viewBox',`0 0 ${canvasWidth} 270`);
  const x=d3.scaleLinear().domain([0,d3.max(valid,value)||1]).range([0,width]);
  const y=d3.scaleBand().domain(valid.map(row=>row.campaign_id)).range([top,top+height]).padding(0.4);
  const svg=d3.select('#bars');
  svg.selectAll('g.plot').data([null]).join('g').attr('class','plot').selectAll('rect.campaign-bar')
    .data(valid,row=>row.campaign_id).join('rect').attr('class','campaign-bar')
    .attr('data-key',row=>row.campaign_id).attr('data-value',value)
    .attr('x',left).attr('y',row=>y(row.campaign_id)).attr('width',row=>x(value(row))).attr('height',y.bandwidth())
    .attr('fill',row=>palette[row.channel]);
  svg.selectAll('text.campaign-label').data(valid,row=>row.campaign_id).join('text').attr('class','campaign-label')
    .attr('x',left-12).attr('y',row=>y(row.campaign_id)+y.bandwidth()/2+5).attr('text-anchor','end').text(row=>row.name);
  svg.selectAll('text.value-label').data(valid,row=>row.campaign_id).join('text').attr('class','value-label')
    .attr('x',row=>left+x(value(row))+8).attr('y',row=>y(row.campaign_id)+y.bandwidth()/2+5).text(row=>def.format(value(row)));
  svg.selectAll('g.axis').data([null]).join('g').attr('class','axis').attr('transform',`translate(${left},230)`)
    .call(d3.axisBottom(x).ticks(canvasWidth<400?2:4).tickFormat(def.format));
  svg.selectAll('text.empty').data(valid.length?[]:[null]).join('text').attr('class','empty').attr('x',left).attr('y',80).text('No known values to compare');
  document.querySelector('#bar-heading').textContent=def.title;
  document.querySelector('#bar-title').textContent=def.title+' ('+def.unit+')';
  const knownSpend=rows.filter(row=>row.spend_cents!==null),total=d3.sum(knownSpend,row=>row.spend_cents);
  const hierarchy={name:'Media spend',children:d3.groups(knownSpend,row=>row.channel).map(([name,children])=>({name,children}))};
  const root=d3.hierarchy(hierarchy).sum(node=>node.children?0:node.spend_cents).sort((a,b)=>b.value-a.value||String(a.data.campaign_id||a.data.name).localeCompare(String(b.data.campaign_id||b.data.name)));
  d3.treemap().size([canvasWidth-20,240]).paddingInner(3)(root);
  const leaves=total>0?root.leaves().filter(node=>node.value>0):[];
  const tiles=d3.select('#treemap').selectAll('g.tile').data(leaves,node=>node.data.campaign_id).join(enter=>{
    const group=enter.append('g').attr('class','tile');group.append('rect');group.append('text');group.append('title');return group;
  }).attr('transform',node=>`translate(${10+node.x0},${10+node.y0})`).attr('data-key',node=>node.data.campaign_id);
  tiles.select('rect').attr('width',node=>node.x1-node.x0).attr('height',node=>node.y1-node.y0).attr('fill',node=>palette[node.data.channel]);
  tiles.select('text').attr('x',12).attr('y',26).style('fill','#fff')
    .text(node=>node.x1-node.x0>180?`${node.data.name} · $${(node.value/100).toFixed(2)}`:node.x1-node.x0>85?`${node.data.campaign_id} · $${(node.value/100).toFixed(2)}`:'');
  tiles.select('title').text(node=>`${node.data.name}: $${(node.value/100).toFixed(2)} media spend`);
  d3.select('#treemap').selectAll('text.empty').data(total>0?[]:[null]).join('text').attr('class','empty').attr('x',20).attr('y',80).text('No positive known spend to display');
  document.querySelector('#tree-note').textContent=`Known spend: $${(total/100).toFixed(2)}. ${rows.length-knownSpend.length} campaign(s) missing spend. Area represents spend, not performance.`;
  const table=d3.select('#values tbody').selectAll('tr').data(rows,row=>row.campaign_id).join('tr');
  table.selectAll('td').data(row=>[row.name,row.spend_cents===null?'Unavailable':definitions.spend_cents.format(row.spend_cents),row.clicks===null?'Unavailable':row.clicks,row.metrics.reported_roas===null?'Unavailable':definitions.reported_roas.format(row.metrics.reported_roas)]).join('td').text(value=>value);
  document.querySelector('#status').textContent=`${rows.length} campaign(s) selected. ${rows.length-valid.length} missing ${def.unit} value(s).`;
}
document.querySelector('#channel').addEventListener('change',render);
document.querySelector('#metric').addEventListener('change',render);
document.querySelector('#empty').addEventListener('click',()=>setData([]));
document.querySelector('#restore').addEventListener('click',()=>setData(source.platform_report.campaigns));
window.addEventListener('resize',render);
window.demo={setData,render,source,selected,get d3Version(){return d3.version;}};
setData(source.platform_report.campaigns);
