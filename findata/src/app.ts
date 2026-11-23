type View = "dashboard" | "sources" | "mapping" | "quality" | "reconciliation" | "certification";
type SourceSummary = {name:string;entity:string;rows:number;columns:number;fields:string[]};
type Mapping = {source:string;target:string;entity:string;transformation:string};
type Rule = {id:string;label:string;description:string;dataset:string;severity:string;evaluated_records:number;failed_records:number;passed_records:number;status:"PASS"|"FAIL"};
type Report = {project:string;generated_at_utc:string;duration_seconds:number;engine:{name:string;version:string;master:string;execution_mode:string};source_summary:SourceSummary[];schema_mapping:Mapping[];quality:{score:number;score_definition:string;total_rules:number;passed_rules:number;failed_rules:number;records_evaluated:number;failed_checks:number;rules:Rule[]};reconciliation:{source_account_count:number;target_account_count:number;source_total_balance:number;target_total_balance:number;balance_difference:number;status:string};certification:{status:string;critical_failures:number;recommendation:string};samples:Record<string,Record<string,unknown>[]>};

const root=document.querySelector<HTMLElement>("#app");
if(!root)throw new Error("FinData root element not found.");
const h=(...parts:unknown[]):string=>parts.map(x=>String(x??"")).join("");
const state:{view:View;report:Report|null;loading:boolean;error:string;modalTitle:string;modalBody:string;uploadMessage:string;reportOrigin:"ci"|"local"|"none";qualityFilter:string}={
 view:"dashboard",report:null,loading:true,error:"",modalTitle:"",modalBody:"",uploadMessage:"",reportOrigin:"none",qualityFilter:"ALL"
};
const NAV:{id:View;icon:string;label:string}[]=[
 {id:"dashboard",icon:"◫",label:"Resumen ejecutivo"},{id:"sources",icon:"▤",label:"Fuentes de datos"},
 {id:"mapping",icon:"⇄",label:"Mapeo de esquemas"},{id:"quality",icon:"✓",label:"Calidad de datos"},
 {id:"reconciliation",icon:"≋",label:"Conciliación"},{id:"certification",icon:"◇",label:"Certificación"}
];
const FALLBACK:SourceSummary[]=[
 {name:"customers_legacy.csv",entity:"customers",rows:30,columns:7,fields:["customer_code","full_name","id_number","email_address","birth_date","customer_status","branch_code"]},
 {name:"accounts_legacy.csv",entity:"accounts",rows:45,columns:8,fields:["acct_no","cust_code","acct_type","currency","opening_dt","balance_amt","branch_code","account_status"]},
 {name:"transactions_legacy.csv",entity:"transactions",rows:120,columns:8,fields:["txn_id","acct_no","txn_datetime","txn_type","amount","currency","channel","reference"]}
];
function esc(v:unknown):string{return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]??c));}
function num(v:number):string{return new Intl.NumberFormat("es-CO").format(v??0);}
function cop(v:number):string{return new Intl.NumberFormat("es-CO",{style:"currency",currency:"COP",maximumFractionDigits:2}).format(v??0);}
function dateText(v:string):string{const d=new Date(v);return Number.isNaN(d.getTime())?v:d.toLocaleString("es-CO",{dateStyle:"medium",timeStyle:"short"});}
function badge(label:string,kind:string):string{return h('<span class="status ',kind,'">',esc(label.replaceAll("_"," ")),'</span>');}
function metric(label:string,value:string,foot:string,icon:string):string{return h('<section class="card"><div class="metric-head"><span>',esc(label),'</span><span class="metric-icon">',icon,'</span></div><div class="metric-value">',value,'</div><div class="metric-foot">',esc(foot),'</div></section>');}
function table(headers:string[],rows:string[][]):string{
 if(!rows.length)return '<div class="empty">No hay información para mostrar.</div>';
 return h('<div class="table-wrap"><table><thead><tr>',headers.map(x=>h('<th>',esc(x),'</th>')).join(""),'</tr></thead><tbody>',
 rows.map(row=>h('<tr>',row.map(cell=>h('<td>',cell,'</td>')).join(""),'</tr>')).join(""),'</tbody></table></div>');
}
function heading(title:string,subtitle:string,action:string=""):string{return h('<div class="page-heading"><div><div class="eyebrow">FinData / ',esc(title),'</div><h1>',esc(title),'</h1><div class="subtitle">',esc(subtitle),'</div></div>',action,'</div>');}

function dashboard():string{
 const r=state.report;
 if(!r)return h(heading("Resumen ejecutivo","Vista general del proceso de integración y certificación."),
  '<div class="empty"><h2>',state.loading?"Cargando reporte de Spark…":"Aún no hay un reporte de Spark disponible",'</h2><p>',
  esc(state.error||"En la demo pública, el reporte se genera automáticamente en GitHub Actions. En local puedes iniciar Spark con Docker Compose."),
  '</p><button class="btn btn-primary" data-action="run-local">Ejecutar Spark local</button></div>');
 const rows=r.source_summary.reduce((s,x)=>s+x.rows,0),q=r.quality,c=r.certification;
 const kind=c.status==="CERTIFIED"?"pass":c.status==="REVIEW_REQUIRED"?"fail":"warn";
 const bars=q.rules.slice(0,8).map(rule=>{
  const rate=rule.evaluated_records?100*rule.failed_records/rule.evaluated_records:0;
  return h('<div class="bar-row"><span title="',esc(rule.label),'">',esc(rule.label.length>18?rule.label.slice(0,17)+"…":rule.label),
   '</span><div class="bar-track"><div class="bar-fill ',rule.failed_records?"fail":"",'" style="width:',Math.max(rule.failed_records?rate:100,2),'%"></div></div><strong>',
   rule.failed_records?num(rule.failed_records)+" fallos":"OK",'</strong></div>');
 }).join("");
 return h(heading("Resumen ejecutivo","Vista general del proceso de integración y certificación.",'<button class="btn" data-action="export-json">↓ Descargar reporte</button>'),
  '<div class="cards">',metric("Registros procesados",num(rows),"Clientes, cuentas y transacciones","▤"),
  metric("Score de controles",q.score.toFixed(2)+"%","Evaluaciones registro-regla","◉"),
  metric("Controles fallidos",num(q.failed_rules),num(q.total_rules)+" reglas ejecutadas","⚑"),
  metric("Estado de certificación",'<span style="font-size:17px">'+esc(c.status.replaceAll("_"," "))+'</span>',num(c.critical_failures)+" fallos críticos","◇"),'</div>',
  '<div class="grid-main"><div><section class="panel"><div class="panel-head"><div><h2>Flujo de procesamiento</h2><div class="panel-sub">De fuentes legadas a evidencia de certificación</div></div>',badge("Spark SQL","pass"),'</div>',
  '<div class="pipeline"><div class="pipe-step"><div class="pipe-num">01 / INGESTA</div><div class="pipe-title">Fuentes</div><div class="pipe-desc">CSV de clientes, cuentas y transacciones</div></div>',
  '<div class="pipe-step"><div class="pipe-num">02 / MAPPING</div><div class="pipe-title">Homologación</div><div class="pipe-desc">Campos, catálogos, fechas y decimales</div></div>',
  '<div class="pipe-step"><div class="pipe-num">03 / PROCESS</div><div class="pipe-title">PySpark + SQL</div><div class="pipe-desc">Transformaciones y reglas de calidad</div></div>',
  '<div class="pipe-step"><div class="pipe-num">04 / CONTROL</div><div class="pipe-title">Certificación</div><div class="pipe-desc">Conciliación y reporte auditable</div></div></div></section>',
  '<section class="panel"><div class="panel-head"><div><h2>Reglas de calidad</h2><div class="panel-sub">Fallos detectados por control</div></div><button class="btn btn-small" data-view="quality">Ver todas</button></div>',bars,'</section></div>',
  '<div><section class="panel"><div class="panel-head"><div><h2>Estado del lote</h2><div class="panel-sub">Resultado de la última ejecución</div></div></div>',
  '<div class="callout ',kind==="fail"?"error":kind==="warn"?"warning":"",'"><strong>',esc(c.status.replaceAll("_"," ")),'</strong><span>',esc(c.recommendation),'</span></div>',
  '<div style="margin-top:15px"><div class="kv"><span>Motor</span><strong>',esc(r.engine.name+" "+r.engine.version),'</strong></div>',
  '<div class="kv"><span>Modo</span><strong>',esc(r.engine.execution_mode+" ("+r.engine.master+")"),'</strong></div>',
  '<div class="kv"><span>Tiempo de ejecución</span><strong>',r.duration_seconds.toFixed(2),' s</strong></div>',
  '<div class="kv"><span>Generado</span><strong>',esc(dateText(r.generated_at_utc)),'</strong></div>',
  '<div class="kv"><span>Origen del reporte</span><strong>',state.reportOrigin==="ci"?"GitHub Actions":"API local",'</strong></div></div></section>',
  '<section class="panel"><div class="panel-head"><div><h2>Conciliación de cuentas</h2><div class="panel-sub">Origen frente al modelo normalizado</div></div>',badge(r.reconciliation.status,r.reconciliation.status==="MATCH"?"pass":"fail"),'</div>',
  '<div class="kv"><span>Cuentas origen</span><strong>',num(r.reconciliation.source_account_count),'</strong></div>',
  '<div class="kv"><span>Cuentas destino</span><strong>',num(r.reconciliation.target_account_count),'</strong></div>',
  '<div class="kv"><span>Diferencia de saldo</span><strong>',cop(r.reconciliation.balance_difference),'</strong></div>',
  '<button class="btn btn-small" style="margin-top:12px" data-view="reconciliation">Ver conciliación →</button></section></div></div>',
  '<div class="footer">Datos sintéticos · Ejecución Spark local · Sin conexión con un banco real</div>');
}

function sources():string{
 const list=state.report?.source_summary??FALLBACK;
 const rows=list.map(s=>[h('<strong>',esc(s.name),'</strong>'),esc(s.entity),num(s.rows),num(s.columns),
  h('<button class="btn btn-small" data-action="preview-source" data-source="',esc(s.name),'">Vista previa</button>')]);
 return h(heading("Fuentes de datos","Exploración de estructuras CSV de un core bancario legado."),
  '<section class="panel"><div class="panel-head"><div><h2>Inventario de fuentes</h2><div class="panel-sub">Archivos de entrada y estructura detectada</div></div>',badge("3 fuentes","neutral"),'</div>',
  table(["Archivo","Entidad","Registros","Columnas","Acción"],rows),'</section>',
  '<section class="panel"><div class="panel-head"><div><h2>Perfilador de archivos CSV</h2><div class="panel-sub">Carga local en el navegador: inspecciona columnas, nulos y filas de muestra; no envía el archivo al servidor.</div></div></div>',
  '<div class="dropzone"><strong>Selecciona un archivo CSV para perfilarlo</strong><div class="subtitle">El archivo se procesa únicamente en esta sesión del navegador.</div><input id="csv-upload" type="file" accept=".csv,text/csv"></div>',
  '<div id="upload-result" style="margin-top:14px">',state.uploadMessage,'</div></section>',
  '<div class="callout">La exploración identifica estructura y volumen. La transformación bancaria del conjunto demostrativo se ejecuta en el pipeline real de PySpark y Spark SQL.</div>');
}
function mapping():string{
 const list=state.report?.schema_mapping??[];
 const rows=list.map(m=>['<span class="mono">'+esc(m.entity)+'</span>','<span class="mono">'+esc(m.source)+'</span>','<strong class="mono">'+esc(m.target)+'</strong>',esc(m.transformation)]);
 return h(heading("Mapeo de esquemas","Correspondencia explícita entre campos Legacy y modelo destino.",'<input id="mapping-search" class="mapping-search" type="search" placeholder="Buscar campo o entidad…">'),
  list.length?table(["Entidad","Campo origen","Campo destino","Transformación"],rows):'<div class="empty">El mapeo estará disponible cuando se cargue el reporte Spark.</div>',
  '<div class="callout" style="margin-top:16px">El mapeo documenta la semántica del campo, tipo destino y transformación aplicada. Las relaciones se validan con reglas de integridad referencial.</div>');
}
function quality():string{
 const rules=state.report?.quality.rules??[];
 const filtered=rules.filter(r=>state.qualityFilter==="ALL"||(state.qualityFilter==="FAIL"&&r.status==="FAIL")||(state.qualityFilter==="PASS"&&r.status==="PASS"));
 const rows=filtered.map(r=>[h('<strong>',esc(r.label),'</strong><div class="muted" style="font-size:9px;margin-top:3px">',esc(r.description),'</div>'),
  esc(r.dataset),esc(r.severity),num(r.evaluated_records),'<strong>'+num(r.failed_records)+'</strong>',
  badge(r.status,r.status==="PASS"?"pass":r.severity==="ERROR"?"fail":"warn")]);
 return h(heading("Calidad de datos","Reglas de integridad, unicidad, obligatoriedad y dominios permitidos."),
  '<section class="panel"><div class="panel-head"><div><h2>Controles ejecutados</h2><div class="panel-sub">',rules.length,' reglas definidas sobre tres entidades</div></div>',
  '<select id="quality-filter" class="btn"><option value="ALL" ',state.qualityFilter==="ALL"?"selected":"",'">Todas las reglas</option><option value="FAIL" ',state.qualityFilter==="FAIL"?"selected":"",'">Con fallos</option><option value="PASS" ',state.qualityFilter==="PASS"?"selected":"",'">Aprobadas</option></select></div>',
  rules.length?table(["Regla","Entidad","Severidad","Evaluados","Fallos","Resultado"],rows):'<div class="empty">Ejecuta el pipeline Spark para consultar los controles.</div>','</section>',
  '<div class="callout warning">Un control fallido no siempre significa que todo el lote deba rechazarse. La severidad y las reglas críticas determinan si la certificación puede avanzar o requiere revisión.</div>');
}
function reconciliation():string{
 const r=state.report?.reconciliation;
 if(!r)return h(heading("Conciliación","Comparación de métricas agregadas entre origen y destino."),'<div class="empty">No hay resultado de conciliación disponible.</div>');
 const ok=r.status==="MATCH";
 return h(heading("Conciliación","Comparación de métricas agregadas entre origen y modelo destino.",badge(r.status,ok?"pass":"fail")),
  '<div class="cards">',metric("Cuentas en origen",num(r.source_account_count),"Sistema Legacy","▤"),
  metric("Cuentas en destino",num(r.target_account_count),"Modelo normalizado","▤"),
  metric("Saldo total origen",cop(r.source_total_balance),"DECIMAL(18,2)","$"),
  metric("Saldo total destino",cop(r.target_total_balance),"DECIMAL(18,2)","$"),'</div>',
  '<section class="panel"><div class="panel-head"><div><h2>Resultado de conciliación</h2><div class="panel-sub">Control de conteo y suma de saldos</div></div>',badge(r.status,ok?"pass":"fail"),'</div>',
  '<div class="score-layout"><div class="score-ring" style="--score:',ok?100:0,'%"><span>',ok?"100%":"0%",'</span></div><div><h2>',ok?"Los totales coinciden":"Se encontraron diferencias",'</h2><p class="subtitle">Diferencia de cuentas: ',num(r.source_account_count-r.target_account_count),'<br>Diferencia de saldo: ',cop(r.balance_difference),'</p></div></div></section>',
  '<div class="callout">Esta conciliación compara cantidad de cuentas y saldo agregado del archivo legado con los valores transformados. En un escenario real se ampliarían controles por moneda, sucursal, producto y fecha de corte.</div>');
}
function certification():string{
 const r=state.report;if(!r)return h(heading("Certificación","Evidencias y decisión del lote de datos."),'<div class="empty">No existe un reporte. Ejecuta el pipeline.</div>');
 const c=r.certification,kind=c.status==="CERTIFIED"?"pass":c.status==="REVIEW_REQUIRED"?"fail":"warn";
 return h(heading("Certificación","Resultado de controles, conciliación y evidencia de ejecución.",badge(c.status,kind)),
  '<section class="panel"><div class="score-layout"><div class="score-ring" style="--score:',r.quality.score,'%"><span>',r.quality.score.toFixed(1),'%</span></div><div><div class="eyebrow">Resultado del lote</div><h1 style="font-size:22px">',esc(c.status.replaceAll("_"," ")),'</h1><div class="subtitle">',esc(c.recommendation),'</div><div style="margin-top:10px">',badge(c.critical_failures+" fallos críticos",c.critical_failures?"fail":"pass"),'</div></div></div></section>',
  '<section class="panel"><div class="panel-head"><div><h2>Resumen de certificación</h2><div class="panel-sub">Evidencia de la ejecución de Spark</div></div></div>',
  '<div class="kv"><span>Motor y versión</span><strong>',esc(r.engine.name+" "+r.engine.version),'</strong></div>',
  '<div class="kv"><span>Fecha de ejecución</span><strong>',esc(dateText(r.generated_at_utc)),'</strong></div>',
  '<div class="kv"><span>Duración</span><strong>',r.duration_seconds.toFixed(2),' segundos</strong></div>',
  '<div class="kv"><span>Reglas aprobadas</span><strong>',num(r.quality.passed_rules),' / ',num(r.quality.total_rules),'</strong></div>',
  '<div class="kv"><span>Reglas con fallos</span><strong>',num(r.quality.failed_rules),'</strong></div>',
  '<div class="kv"><span>Verificaciones fallidas</span><strong>',num(r.quality.failed_checks),'</strong></div>',
  '<div class="kv"><span>Conciliación de cuentas</span><strong>',esc(r.reconciliation.status),'</strong></div></section>',
  '<div class="callout warning">El lote demostrativo contiene anomalías intencionales. El resultado esperado es REVIEW_REQUIRED: el motor debe detectar las excepciones, no aprobar automáticamente información inconsistente.</div>',
  '<div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:15px"><button class="btn btn-primary" data-action="export-json">↓ Descargar evidencia JSON</button><button class="btn" data-action="export-errors">↓ Descargar reglas fallidas CSV</button></div>');
}
function content():string{
 switch(state.view){case "dashboard":return dashboard();case "sources":return sources();case "mapping":return mapping();case "quality":return quality();case "reconciliation":return reconciliation();case "certification":return certification();}
}
function render():void{
 const nav=NAV.map(n=>h('<button class="',state.view===n.id?"active":"",'" data-view="'',n.id,'"><span class="nav-icon">',n.icon,'</span><span>',n.label,'</span></button>')).join("");
 root!.innerHTML=h('<div class="shell"><aside class="sidebar"><div class="brand"><div class="brand-mark">FD</div><div><div class="brand-name">FinData</div><div class="brand-sub">Data Engineering Lab</div></div></div>',
 '<div><div class="nav-label">Workspace</div><nav class="nav">',nav,'</nav></div>',
 '<div class="sidebar-bottom"><div class="env-pill"><span class="dot"></span> ',state.reportOrigin==="ci"?"CI report ready":state.reportOrigin==="local"?"Local Spark API":"Awaiting Spark report",'</div><div class="sidebar-note">Financial Data Integration<br>Mapping · Quality · Certification</div></div></aside>',
 '<main class="main"><header class="topbar"><div><div class="eyebrow">Financial data operations</div><div class="top-title">',esc(NAV.find(n=>n.id===state.view)?.label??"FinData"),'</div></div>',
 '<div class="top-actions"><span class="tag">● ',state.report?"Reporte disponible":"Sin reporte",'</span><button class="btn btn-small" data-action="run-local">▶ Ejecutar Spark local</button><div class="avatar">FD</div></div></header>',
 '<div class="content">',content(),'<div class="footer">FinData Portfolio Project · Datos sintéticos · Sin afiliación con entidades financieras</div></div></main></div>',
 state.modalTitle?h('<div class="modal-backdrop"><section class="modal" role="dialog" aria-modal="true"><div class="modal-head"><h2>',esc(state.modalTitle),'</h2><button class="btn btn-small" data-action="close-modal">Cerrar ✕</button></div>',state.modalBody,'</section></div>'):"");
}
function modal(title:string,body:string):void{state.modalTitle=title;state.modalBody=body;render();}
function download(name:string,text:string,type:string):void{
 const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement("a");a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
}
function parseCsv(text:string):string[][]{
 const rows:string[][]=[];let row:string[]=[],field="",quoted=false;
 for(let i=0;i<text.length;i++){const ch=text[i];
  if(ch==='"'&&quoted&&text[i+1]==='"'){field+='"';i++;}
  else if(ch==='"'){quoted=!quoted;}
  else if(ch===","&&!quoted){row.push(field);field="";}
  else if((ch==="\n"||ch==="\r")&&!quoted){if(ch==="\r"&&text[i+1]==="\n")i++;row.push(field);if(row.some(x=>x!==""))rows.push(row);row=[];field="";}
  else field+=ch;
 }
 if(field.length||row.length){row.push(field);if(row.some(x=>x!==""))rows.push(row);}return rows;
}
async function previewSource(filename:string):Promise<void>{
 try{const res=await fetch(new URL("data/"+encodeURIComponent(filename),document.baseURI));if(!res.ok)throw new Error("No fue posible descargar la fuente.");
  const rows=parseCsv(await res.text()),heads=rows[0]??[],body=rows.slice(1,11).map(row=>h("<tr>",heads.map((_,i)=>h("<td>",esc(row[i]??""),"</td>")).join(""),"</tr>")).join("");
  modal(filename,h('<p class="subtitle">',num(Math.max(rows.length-1,0)),' registros · ',heads.length,' columnas · Muestra de máximo 10 filas</p><div class="table-wrap"><table><thead><tr>',heads.map(x=>h("<th>",esc(x),"</th>")).join(""),'</tr></thead><tbody>',body,'</tbody></table></div><p style="margin-top:14px"><button class="btn" data-action="download-source" data-source="',esc(filename),'">Descargar CSV</button></p>'));
 }catch(e){modal("Fuente no disponible",h('<div class="callout warning">',esc(e instanceof Error?e.message:String(e)),'</div>'));}
}
async function downloadSource(filename:string):Promise<void>{
 const res=await fetch(new URL("data/"+encodeURIComponent(filename),document.baseURI));if(!res.ok){modal("Descarga no disponible","No se encontró el archivo de fuente.");return;}
 download(filename,await res.text(),"text/csv;charset=utf-8");
}
async function profileUpload(file:File):Promise<void>{
 const rows=parseCsv(await file.text());if(rows.length<2){state.uploadMessage='<div class="callout warning">El archivo está vacío o no tiene filas de datos.</div>';render();return;}
 const headers=rows[0],data=rows.slice(1),nulls=headers.map((name,i)=>({name,count:data.filter(r=>!String(r[i]??"").trim()).length}));
 const duplicates=data.length-new Set(data.map(r=>JSON.stringify(r))).size;
 state.uploadMessage=h('<div class="cards" style="margin-top:12px">',metric("Filas",num(data.length),"Leídas en navegador","▤"),
  metric("Columnas",num(headers.length),"Encabezados detectados","▥"),metric("Filas duplicadas",num(duplicates),"Comparación exacta","↻"),
  metric("Celdas vacías",num(nulls.reduce((s,x)=>s+x.count,0)),"Valores vacíos","∅"),'</div>',
  table(["Columna","Celdas vacías"],nulls.map(x=>[esc(x.name),num(x.count)])),
  '<p class="subtitle">Perfilamiento local de ',esc(file.name),'. El archivo no se transmitió ni se guardó en el servidor.</p>');
 render();
}
async function runLocal():Promise<void>{
 if(location.hostname!=="localhost"&&location.hostname!=="127.0.0.1"){
  modal("Ejecución Spark local",'<div class="callout">La demo pública presenta el último reporte generado en GitHub Actions. Para ejecutar un nuevo lote con Spark, inicia el entorno local con Docker Compose.</div><pre class="mono" style="white-space:pre-wrap;background:#f5f7f9;padding:14px;border-radius:8px;margin-top:12px">cd findata\ndocker compose up --build</pre><p class="subtitle">Abre http://localhost:8080 y pulsa de nuevo “Ejecutar Spark local”.</p>');return;
 }
 try{const res=await fetch("http://localhost:8000/api/run",{method:"POST"});if(!res.ok)throw new Error(await res.text());
  state.report=await res.json() as Report;state.reportOrigin="local";state.view="dashboard";state.error="";render();
 }catch(e){modal("No se pudo ejecutar Spark",h('<div class="callout warning">',esc(e instanceof Error?e.message:String(e)),'</div><p class="subtitle">Verifica que Docker esté activo y la API responda en localhost:8000.</p>'));}
}
root.addEventListener("click",async(event:MouseEvent)=>{
 const target=event.target;if(!(target instanceof Element))return;
 if(target.classList.contains("modal-backdrop")){state.modalTitle="";state.modalBody="";render();return;}
 const button=target.closest<HTMLElement>("[data-view],[data-action]");if(!button)return;
 const view=button.dataset.view as View|undefined;if(view){state.view=view;state.modalTitle="";render();return;}
 const action=button.dataset.action;
 if(action==="close-modal"){state.modalTitle="";state.modalBody="";render();}
 else if(action==="run-local")await runLocal();
 else if(action==="preview-source"&&button.dataset.source)await previewSource(button.dataset.source);
 else if(action==="download-source"&&button.dataset.source)await downloadSource(button.dataset.source);
 else if(action==="export-json"&&state.report)download("findata-certification-report.json",JSON.stringify(state.report,null,2),"application/json");
 else if(action==="export-errors"&&state.report){
  const failed=state.report.quality.rules.filter(r=>r.status==="FAIL");
  const lines=["rule_id,label,entity,severity,evaluated_records,failed_records",...failed.map(r=>[r.id,r.label,r.dataset,r.severity,r.evaluated_records,r.failed_records].map(v=>'"'+String(v).replaceAll('"','""')+'"').join(","))];
  download("findata-quality-findings.csv",lines.join("\n"),"text/csv;charset=utf-8");
 }
});
root.addEventListener("change",async(event:Event)=>{
 const target=event.target;
 if(target instanceof HTMLInputElement&&target.id==="csv-upload"&&target.files?.[0])await profileUpload(target.files[0]);
 if(target instanceof HTMLSelectElement&&target.id==="quality-filter"){state.qualityFilter=target.value;render();}
});
root.addEventListener("input",(event:Event)=>{
 const target=event.target;
 if(target instanceof HTMLInputElement&&target.id==="mapping-search"){
  const q=target.value.toLowerCase();
  root!.querySelectorAll<HTMLTableRowElement>(".table-wrap tbody tr").forEach(row=>{row.style.display=row.textContent?.toLowerCase().includes(q)?"":"none";});
 }
});
async function loadReport():Promise<void>{
 try{const res=await fetch(new URL("spark-results.json",document.baseURI),{cache:"no-store"});if(res.ok){state.report=await res.json() as Report;state.reportOrigin="ci";return;}}catch{/* static report is absent in local Docker mode */}
 if(location.hostname==="localhost"||location.hostname==="127.0.0.1"){
  try{const res=await fetch("http://localhost:8000/api/report");if(res.ok){state.report=await res.json() as Report;state.reportOrigin="local";return;}}catch{/* API may not be running yet */}
 }
 state.error="No hay reporte Spark publicado. Revisa el último workflow de GitHub Actions.";
}
loadReport().finally(()=>{state.loading=false;render();});
