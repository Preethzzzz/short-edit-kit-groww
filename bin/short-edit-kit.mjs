#!/usr/bin/env node
/* short-edit-kit-groww: alone, the manual (the whole workflow); else a command. Every pipeline command runs one
   Python script of the kit with the Python that `setup` installed, as an argument list (no shell), and ends with
   one summary line. */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const PKG = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'));
const RUN = process.env.npm_command === 'exec' ? `npx -y ${PKG.name}@latest` : 'short-edit-kit';
const CONFIG = (process.env.SEK_CONFIG || join(homedir(), '.short-edit-kit', 'config.json')).replace(/^~(?=\/)/, homedir());
const REPO = 'Preethzzzz/short-edit-kit-groww';
const MARKET = 'groww-video';

/* command -> [script, what it does] */
const STEPS = {
  init: ['init_job.py', 'job folder from footage + script (DOCX, PDF or text)'],
  key: ['key.py', 'green-screen key (or --plain grade) of the presenter'],
  transcribe: ['transcribe.py', 'Whisper word timings of the raw take'],
  'extra-words': ['extra_words.py', 'spoken words that are not in the script'],
  cuts: ['make_segments.py', 'segments.json: kept takes, cuts, shortened pauses'],
  audio: ['build_audio.py', 'voice track cut to the segments, loudness-normalised'],
  joins: ['check_joins.py', 're-transcribe every join to prove the cut is clean'],
  align: ['align.py', 'script words on the edited timeline'],
  plan: ['build_plan.py', 'plan.json (script phrases) -> edit.json (seconds)'],
  captions: ['captions.py', 'English captions as SRT + VTT'],
  mix: ['build_mix.py', 'voice + music bed + effects, loudness-normalised'],
  render: ['render.py', 'Remotion render to out/final.mp4 (--test: 10 s sample)'],
  stills: ['stills.py', 'contact sheet of a render'],
  qa: ['qa_check.py', 'deterministic QA (numbers, captions, safe zones, loudness)'],
  openfilm: ['openfilm_export.py', 'only when asked: OpenFilm project (default output stays out/final.mp4)'],
};

const say = (line) => console.log(line);
const fail = (line, code = 1) => { console.error(`${PKG.name}: ${line}`); process.exit(code); };

function usage() {
  const pad = Math.max(...Object.keys(STEPS).map((k) => k.length));
  return [
    `Usage: ${RUN} <command> [args]   (alone: the manual)`,
    '',
    `  setup [--tools-dir DIR] [--skip-render]   install or verify ffmpeg, Python + faster-whisper, model, Remotion; test render`,
    `  install-claude                            add the skills and agents to Claude Code (plugin ${PKG.name}@${MARKET})`,
    `  doctor                                    show the config setup wrote`,
    ...Object.entries(STEPS).map(([k, [, what]]) => `  ${k.padEnd(pad)}  ${what}`),
    '',
    `  ${RUN} <command> --help   that command's arguments`,
  ].join('\n');
}

/* the script's own docstring, with its file name replaced by the command */
function scriptHelp(cmd) {
  const [script] = STEPS[cmd];
  const src = readFileSync(join(ROOT, 'scripts', script), 'utf8');
  const doc = (src.match(/^"""([\s\S]*?)"""/) || [, ''])[1].trim();
  return doc.replaceAll(new RegExp(`(python3? )?${script.replace('.', '\\.')}`, 'g'), `${RUN} ${cmd}`);
}

function config() {
  if (!existsSync(CONFIG)) fail(`no config at ${CONFIG}: run \`${RUN} setup\` first`);
  return JSON.parse(readFileSync(CONFIG, 'utf8'));
}

function python3() {
  const cands = [process.env.SEK_PYTHON, 'python3', '/usr/bin/python3'].filter(Boolean);
  for (const c of cands) {
    const r = spawnSync(c, ['-c', 'import sys;print(sys.version_info >= (3, 9))'], { encoding: 'utf8' });
    if (r.status === 0 && r.stdout.trim() === 'True') return c;
  }
  fail('Python 3.9+ not found (macOS: run `xcode-select --install`, or install from python.org; no admin needed for a user install)');
}

function runPy(py, script, args) {
  const t0 = Date.now();
  const r = spawnSync(py, ['-I', join(ROOT, 'scripts', script), ...args], { stdio: 'inherit' });
  const secs = ((Date.now() - t0) / 1000).toFixed(1);
  if (r.error) fail(`${script}: ${r.error.message}`);
  return { code: r.status ?? 1, secs };
}

/* newer version on npm: one line, checked only when the manual is shown, never waits more than 1.5 s */
async function updateNotice() {
  try {
    const res = await fetch(`https://registry.npmjs.org/${PKG.name}/latest`, { signal: AbortSignal.timeout(1500) });
    const { version } = await res.json();
    const newer = (a, b) => { const x = a.split('.').map(Number), y = b.split('.').map(Number); for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i]; return false; };
    if (version && newer(version, PKG.version)) console.error(`${PKG.name} ${version} is out (this is ${PKG.version}): run it as \`npx -y ${PKG.name}@latest\`.`);
  } catch { /* offline: say nothing */ }
}

function installClaude() {
  const claude = spawnSync('claude', ['--version'], { encoding: 'utf8' });
  if (claude.status !== 0) {
    say('Claude Code CLI not found. In Claude Code, run:');
    say(`  /plugin marketplace add ${REPO}`);
    say(`  /plugin install ${PKG.name}@${MARKET}`);
    process.exit(1);
  }
  const cl = (...a) => spawnSync('claude', ['plugin', ...a], { encoding: 'utf8' });
  const list = cl('marketplace', 'list').stdout || '';
  if (!list.includes(MARKET)) {
    const r = cl('marketplace', 'add', REPO);
    if (r.status !== 0) fail(`marketplace add failed: ${(r.stderr || r.stdout).trim().slice(-300)}`);
    say(`ADDED     marketplace ${MARKET} (github.com/${REPO})`);
  } else {
    cl('marketplace', 'update', MARKET);
    say(`UPDATED   marketplace ${MARKET}`);
  }
  const id = `${PKG.name}@${MARKET}`;
  let r = cl('install', id);
  const out = `${r.stdout}${r.stderr}`;
  if (r.status !== 0 && !/already installed/i.test(out)) fail(`install failed: ${out.trim().slice(-300)}`);
  if (/already installed/i.test(out)) {
    r = cl('update', id);
    say(`UPDATED   plugin ${id}: ${(r.stdout || r.stderr).trim().split('\n').pop()}`);
  } else say(`INSTALLED plugin ${id}`);
  say(`install-claude done: skills edit-short, format-ipo-day-roundup, format-data-explainer, setup; agents content-strategist, infographics, motion-graphics, editor, qa-checker. Restart Claude Code to load them.`);
}

const argv = process.argv.slice(2);
const cmd = argv[0];

if (!cmd) {
  await updateNotice();
  say(readFileSync(join(ROOT, 'MANUAL.md'), 'utf8').replaceAll('npx -y short-edit-kit-groww@latest', RUN));
} else if (cmd === '--version' || cmd === '-v') {
  say(PKG.version);
} else if (cmd === 'help' || cmd === '--help' || cmd === '-h') {
  say(argv[1] && STEPS[argv[1]] ? scriptHelp(argv[1]) : usage());
} else if (cmd === 'setup') {
  if (argv.includes('--help')) { say(readFileSync(join(ROOT, 'scripts', 'setup.py'), 'utf8').match(/^"""([\s\S]*?)"""/)[1].trim().replaceAll('python3 setup.py', `${RUN} setup`)); process.exit(0); }
  const { code, secs } = runPy(python3(), 'setup.py', argv.slice(1));
  say(code === 0 ? `setup done in ${secs}s. Next: \`${RUN} install-claude\`, then ask Claude Code to edit a Short.` : `setup FAILED (exit ${code}) after ${secs}s: fix the FAIL lines above and run it again.`);
  process.exit(code);
} else if (cmd === 'install-claude') {
  installClaude();
} else if (cmd === 'doctor') {
  const c = config();
  for (const [k, v] of Object.entries(c)) say(`${existsSync(String(v)) || k === 'brand' ? 'OK  ' : 'MISSING'} ${k.padEnd(12)} ${v}`);
  say(`config ${CONFIG}; kit ${PKG.version} at ${ROOT}`);
} else if (STEPS[cmd]) {
  if (argv.includes('--help') || argv.includes('-h') || argv.length === 1) { say(scriptHelp(cmd)); process.exit(argv.length === 1 ? 2 : 0); }
  const py = config().python;
  if (!py || !existsSync(py)) fail(`Python from setup not found (${py}): run \`${RUN} setup\``);
  const { code, secs } = runPy(py, STEPS[cmd][0], argv.slice(1));
  say(code === 0 ? `${cmd} done in ${secs}s` : `${cmd} FAILED (exit ${code}) after ${secs}s`);
  process.exit(code);
} else {
  fail(`unknown command \`${cmd}\`\n\n${usage()}`, 2);
}
