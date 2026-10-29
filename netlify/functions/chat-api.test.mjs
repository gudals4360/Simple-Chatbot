import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import handler from './chat-api.mjs';

test('persona profile, extended history and Gemini temperature reach the provider', async () => {
  const originalFetch = globalThis.fetch;
  const originalKey = process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY = 'test-only';
  let payload;
  globalThis.fetch = async (_url, options) => {
    payload = JSON.parse(options.body);
    return new Response('data: '+JSON.stringify({candidates:[{content:{parts:[{text:'고맙긴 한데 좀 미안하죠.'}]}}]})+'\n\n');
  };
  try {
    const messages = Array.from({length:39}, (_,i) => ({role:i%2?'assistant':'user',content:i===0?'저는 계단 없는 길이 좋아요.':i===38?'그때 기분은요?':'점심 이야기 '+i}));
    const response = await handler(new Request('https://test.local/api/chat', {method:'POST',body:JSON.stringify({room_id:'donggyu',provider:'gemini',messages})}));
    assert.equal(response.status,200);
    assert.equal(await response.text(),'고맙긴 한데 좀 미안하죠.');
    assert.equal(payload.contents.length,39);
    assert.equal(payload.contents[0].parts[0].text,messages[0].content);
    assert.equal(payload.contents.at(-1).parts[0].text,'그때 기분은요?');
    assert.equal(payload.generationConfig.temperature,0.85);
    const system=payload.systemInstruction.parts[0].text;
    const profiles=JSON.parse(fs.readFileSync(new URL('../../Simple Chat bot/backend/data/personas.json',import.meta.url),'utf8'));
    assert.ok(system.includes(profiles.find(p=>p.id==='donggyu').bio));
    const policy=fs.readFileSync(new URL('../../Simple Chat bot/backend/knowledge/donggyu_chat.md',import.meta.url),'utf8').trim();
    assert.ok(system.includes(policy));
    assert.ok(system.includes('합성 페르소나'));
    const other=await handler(new Request('https://test.local/api/chat',{method:'POST',body:JSON.stringify({room_id:'seondong',provider:'gemini',messages:[{role:'user',content:'안녕'}]})}));
    await other.text();
    assert.ok(!payload.systemInstruction.parts[0].text.includes(policy));
  } finally {
    globalThis.fetch=originalFetch;
    if(originalKey===undefined) delete process.env.GEMINI_API_KEY; else process.env.GEMINI_API_KEY=originalKey;
  }
});

test('oversized history is rejected before calling the provider', async () => {
  const response=await handler(new Request('https://test.local/api/chat',{method:'POST',body:JSON.stringify({room_id:'donggyu',messages:Array.from({length:41},()=>({role:'user',content:'안녕'}))})}));
  assert.equal(response.status,422);
});

test('standalone and modular UI retain complete pairs within the API limit', () => {
  for(const path of ['../../Simple Chat bot/frontend/js/ui/chat.js','../../Simple Chat bot/standalone.html']) {
    const source=fs.readFileSync(new URL(path,import.meta.url),'utf8');
    assert.ok(source.includes('R.history.slice(-39)'));
  }
  const html=fs.readFileSync(new URL('../../Simple Chat bot/standalone.html',import.meta.url),'utf8');
  const policy=JSON.parse(html.match(/const DONGGYU_CHAT = (".*");/)[1]);
  assert.equal(policy.trim(),fs.readFileSync(new URL('../../Simple Chat bot/backend/knowledge/donggyu_chat.md',import.meta.url),'utf8').trim());
  const start=html.indexOf('  function personaPrompt(d) {');
  const end=html.indexOf('\n  }',start)+4;
  const profiles=JSON.parse(fs.readFileSync(new URL('../../Simple Chat bot/backend/data/personas.json',import.meta.url),'utf8'));
  const prompt=vm.runInNewContext(html.slice(start,end)+'\npersonaPrompt(profile)',{DONGGYU_CHAT:policy,profile:profiles.find(p=>p.id==='donggyu')});
  assert.ok(prompt.includes(policy));
  assert.ok(!html.slice(html.indexOf('  function systemPrompt(extra)'),start).includes("${d.id === 'donggyu'"));
});
