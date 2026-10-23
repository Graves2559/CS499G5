import http from 'node:http';
import fs from 'node:fs/promises';
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml'};
http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://localhost');const file=url.pathname==='/'?'index.html':url.pathname.slice(1);if(!['index.html','app.js','style.css','favicon.svg'].includes(file)){res.writeHead(404).end();return;}const data=await fs.readFile('dist/'+file);res.writeHead(200,{'Content-Type':types[file.slice(file.lastIndexOf('.'))]});res.end(data);}catch{res.writeHead(500).end();}}).listen(5173,'127.0.0.1',()=>console.log('Local: http://127.0.0.1:5173'));
