html_content = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Picking Stats</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0;padding:16px 16px 140px;min-height:100vh}
.header{text-align:center;margin-bottom:24px}
.header h1{font-size:28px;font-weight:700;background:linear-gradient(135deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.header .subtitle{color:#94a3b8;font-size:14px}
.nav-tabs{display:flex;gap:8px;overflow-x:auto;padding:8px 0;margin-bottom:20px}
.nav-tab{flex-shrink:0;padding:10px 20px;border-radius:12px;background:rgba(30,41,59,0.5);border:1px solid rgba(100,116,139,0.2);color:#94a3b8;font-size:14px;font-weight:600;cursor:pointer}
.nav-tab.active{background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:white}
.section{display:none}
.section.active{display:block}
.card{background:rgba(30,41,59,0.7);border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 4px 6px rgba(0,0,0,0.3);border:1px solid rgba(100,116,139,0.2)}
.card-title{font-size:16px;font-weight:600;margin-bottom:16px;color:#cbd5e1}
.stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.stat{background:rgba(15,23,42,0.5);padding:16px;border-radius:12px}
.stat-label{font-size:12px;color:#94a3b8;margin-bottom:6px}
.stat-value{font-size:24px;font-weight:700;color:#f1f5f9}
.stat-value.highlight{color:#3b82f6}
.stat-value.success{color:#10b981}
.trend{display:inline-block;padding:4px 10px;border-radius:12px;font-size:13px;margin-top:8px}
.trend.up{background:rgba(16,185,129,0.2);color:#10b981}
.trend.down{background:rgba(239,68,68,0.2);color:#ef4444}
.order-list{list-style:none}
.order-item{background:rgba(15,23,42,0.5);padding:14px;border-radius:10px;margin-bottom:10px;display:flex;justify-content:space-between}
.order-cliente{font-weight:600;color:#f1f5f9}
.order-details{font-size:13px;color:#94a3b8}
.order-speed{font-size:18px;font-weight:700;color:#3b82f6}
.best-item{background:rgba(15,23,42,0.5);padding:12px;border-radius:10px;margin-bottom:10px;border-left:3px solid #3b82f6}
.best-title{font-size:13px;color:#3b82f6;font-weight:600}
.best-value{font-size:20px;font-weight:700;color:#f1f5f9}
.best-details{font-size:12px;color:#94a3b8}
.refresh-btn{position:fixed;bottom:80px;right:20px;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border:none;color:white;font-size:24px;cursor:pointer;z-index:100}
.loading{text-align:center;padding:40px;color:#94a3b8}
.map-container{background:rgba(15,23,42,0.5);border-radius:12px;padding:16px;overflow:auto}
.map-svg{width:100%;height:auto;max-height:70vh}
.legend{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:16px}
.legend-item{display:flex;align-items:center;gap:8px;font-size:12px;color:#cbd5e1}
.legend-color{width:20px;height:20px;border-radius:4px;flex-shrink:0}
.zone-label{font-size:10px;fill:#f1f5f9;pointer-events:none}
.zone-rect{stroke-width:1;stroke:rgba(255,255,255,0.1)}
.zone-rect:hover{stroke:#3b82f6;stroke-width:2}
.wall-rect{fill:none;stroke-width:2}
.aisle-rect{opacity:0.5}
</style>
</head>
<body>
<div class="header">
<h1>📊 Picking Stats</h1>
<div class="subtitle" id="lastUpdate">Cargando...</div>
</div>
<div class="nav-tabs">
<div class="nav-tab active" onclick="showSection('overview')">📊 Resumen</div>
<div class="nav-tab" onclick="showSection('records')">🏆 Records</div>
<div class="nav-tab" onclick="showSection('orders')">📋 Pedidos</div>
<div class="nav-tab" onclick="showSection('map')">🗺️ Mapa</div>
</div>
<div id="content">
<div class="loading">Cargando datos...</div>
</div>
<button class="refresh-btn" onclick="refreshData()">🔄</button>
<script>
let currentSection='overview',cachedData=null,layoutData=null;
function showSection(s){currentSection=s;document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));event.target.classList.add('active');if(s==='map'&&!layoutData)fetchLayout();if(cachedData)renderDashboard(cachedData);}
async function fetchData(){try{const [today,week,month,recent,stats,bests,allTime]=await Promise.all([fetch('/api/today').then(r=>r.json()),fetch('/api/week').then(r=>r.json()),fetch('/api/month').then(r=>r.json()),fetch('/api/recent').then(r=>r.json()),fetch('/api/stats').then(r=>r.json()),fetch('/api/bests').then(r=>r.json()),fetch('/api/all_time').then(r=>r.json())]);cachedData={today,week,month,recent,stats,bests,allTime};renderDashboard(cachedData);updateLastRefresh();}catch(e){document.getElementById('content').innerHTML='<div class="loading">Error al cargar datos</div>';}}
async function fetchLayout(){try{const r=await fetch('/api/layout');layoutData=await r.json();renderDashboard(cachedData);}catch(e){console.error('Error loading layout:',e);}}
function renderDashboard(d){const {today,week,month,recent,stats,bests,allTime}=d;const c=document.getElementById('content');let h='';if(currentSection==='overview'){h=`<div class="section active"><div class="card"><div class="card-title">Hoy</div><div class="stats-grid"><div class="stat"><div class="stat-label">Pedidos</div><div class="stat-value highlight">${today.orders}</div></div><div class="stat"><div class="stat-label">SKUs</div><div class="stat-value">${today.skus}</div></div><div class="stat"><div class="stat-label">Velocidad</div><div class="stat-value success">${today.speed}</div></div><div class="stat"><div class="stat-label">Ganado</div><div class="stat-value highlight">$${today.earned.toLocaleString()}</div></div></div></div><div class="card"><div class="card-title">Esta Semana</div><div class="stats-grid"><div class="stat"><div class="stat-label">Pedidos</div><div class="stat-value">${week.orders}</div></div><div class="stat"><div class="stat-label">SKUs</div><div class="stat-value">${week.skus}</div></div><div class="stat"><div class="stat-label">Velocidad</div><div class="stat-value">${week.speed}</div></div><div class="stat"><div class="stat-label">Ganado</div><div class="stat-value highlight">$${week.earned.toLocaleString()}</div></div></div></div><div class="card"><div class="card-title">Este Mes</div><div class="stats-grid"><div class="stat"><div class="stat-label">Pedidos</div><div class="stat-value">${month.orders}</div></div><div class="stat"><div class="stat-label">SKUs</div><div class="stat-value">${month.skus}</div></div><div class="stat"><div class="stat-label">Velocidad</div><div class="stat-value">${month.speed}</div></div><div class="stat"><div class="stat-label">Ganado</div><div class="stat-value highlight">$${month.earned.toLocaleString()}</div></div></div></div><div class="card"><div class="card-title">Tendencia</div><div style="text-align:center"><div style="font-size:32px;font-weight:700;margin:16px 0">${stats.recent_speed} SKUs/h</div><div class="trend ${stats.change_percent>0?'up':stats.change_percent<0?'down':'neutral'}">${stats.change_percent>0?'↑':stats.change_percent<0?'↓':'→'} ${Math.abs(stats.change_percent)}%</div></div></div><div class="card"><div class="card-title">Total</div><div class="stats-grid"><div class="stat"><div class="stat-label">Total Ganado</div><div class="stat-value highlight">$${allTime.total_earned.toLocaleString()}</div></div><div class="stat"><div class="stat-label">Pedidos</div><div class="stat-value">${allTime.total_orders}</div></div><div class="stat"><div class="stat-label">SKUs</div><div class="stat-value">${allTime.total_skus.toLocaleString()}</div></div><div class="stat"><div class="stat-label">Velocidad</div><div class="stat-value">${allTime.avg_speed}</div></div></div></div></div>`;}else if(currentSection==='records'){h=`<div class="section active"><div class="card"><div class="card-title">Records Personales</div>${bests.fastest_order?`<div class="best-item"><div class="best-title">Mas Rapido</div><div class="best-value">${bests.fastest_order.time} mins</div><div class="best-details">${bests.fastest_order.skus} SKUs - ${bests.fastest_order.cliente}</div></div>`:''}${bests.most_skus?`<div class="best-item"><div class="best-title">Mas SKUs</div><div class="best-value">${bests.most_skus.skus} SKUs</div><div class="best-details">${bests.most_skus.time} mins - ${bests.most_skus.cliente}</div></div>`:''}${bests.best_speed?`<div class="best-item"><div class="best-title">Mejor Velocidad</div><div class="best-value">${bests.best_speed.speed} SKUs/h</div><div class="best-details">${bests.best_speed.skus} SKUs - ${bests.best_speed.cliente}</div></div>`:''}  </div></div>`;}else if(currentSection==='orders'){h=`<div class="section active"><div class="card"><div class="card-title">Ultimos Pedidos</div><ul class="order-list">${recent.map(o=>`<li class="order-item"><div><div class="order-cliente">${o.cliente}</div><div class="order-details">${o.fecha} - ${o.skus} SKUs - ${o.tiempo}</div></div><div class="order-speed">${o.speed}</div></li>`).join('')}</ul></div></div>`;}else if(currentSection==='map'){h=layoutData?renderMap(layoutData):'<div class="loading">Cargando mapa...</div>';}c.innerHTML=h;}
function renderMap(layout){const zones=layout.zones||[];const aisles=layout.aisles||[];const walls=layout.walls||[];const width=800;const layoutWidth=3000;const layoutHeight=3300;const zoneTypes={'dry_shelves':{name:'Abarrotes',color:'#f59e0b'},'produce':{name:'Frutas y Verduras',color:'#10b981'},'fridges':{name:'Refrigerados',color:'#06b6d4'},'freezers':{name:'Congelados',color:'#3b82f6'},'chilled_produce':{name:'Refrigerados Frescos',color:'#22c55e'},'prepared_meals':{name:'Comidas Preparadas',color:'#14b8a6'},'cecineria':{name:'Cecinería',color:'#ef4444'},'frontera':{name:'Frontera',color:'#8b5cf6'},'ice_dispenser':{name:'Dispensador Hielo',color:'#0ea5e9'},'bagging':{name:'Mesas Embolsado',color:'#64748b'},'backpacks':{name:'Mochilas',color:'#a855f7'},'handoff':{name:'Despacho/Entrega',color:'#fb923c'},'aisle':{name:'Pasillos',color:'#475569'}};let svg='<div class="section active"><div class="card"><div class="card-title">Mapa de Darkstore</div><div class="map-container">';svg+=`<svg class="map-svg" viewBox="0 ${-layoutHeight} ${layoutWidth} ${layoutHeight}" xmlns="http://www.w3.org/2000/svg">`;walls.forEach(w=>{svg+=`<rect class="wall-rect" x="${w.x}" y="${w.y}" width="${w.width}" height="${w.height}" stroke="${w.border_color||'#64748b'}"/>`;});zones.forEach(z=>{svg+=`<rect class="zone-rect" x="${z.x}" y="${z.y}" width="${z.width}" height="${z.height}" fill="${z.color}"/>`;if(z.label)svg+=`<text class="zone-label" x="${z.x+z.width/2}" y="${z.y+z.height/2}" text-anchor="middle" dominant-baseline="middle">${z.label}</text>`;});aisles.forEach(a=>{svg+=`<rect class="aisle-rect" x="${a.x}" y="${a.y}" width="${a.width}" height="${a.height}" fill="${a.color}"/>`;if(a.label)svg+=`<text class="zone-label" x="${a.x+a.width/2}" y="${a.y+a.height/2}" text-anchor="middle" dominant-baseline="middle">${a.label}</text>`;});svg+='</svg></div>';svg+='<div class="legend">';Object.entries(zoneTypes).forEach(([key,val])=>{svg+=`<div class="legend-item"><div class="legend-color" style="background:${val.color}"></div><span>${val.name}</span></div>`;});svg+='</div></div></div>';return svg;}
function updateLastRefresh(){const n=new Date();const t=n.toLocaleTimeString('es-CL',{hour:'2-digit',minute:'2-digit'});document.getElementById('lastUpdate').textContent=`Ultima actualizacion: ${t}`;}
function refreshData(){fetchData();}
fetchData();
setInterval(fetchData,120000);
</script>
</body>
</html>"""

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
    
print("✅ HTML file written successfully!")
