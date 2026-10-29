import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import handler from './chat-api.mjs';

test('persona profile, photo and history reach Gemini with compatible options', async () => {
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
    const response = await handler(new Request('https://test.local/api/chat', {method:'POST',body:JSON.stringify({room_id:'donggyu',provider:'gemini',messages,image:'data:image/jpeg;base64,/9j/2Q=='})}));
    assert.equal(response.status,200);
    assert.equal(await response.text(),'고맙긴 한데 좀 미안하죠.');
    assert.equal(payload.contents.length,39);
    assert.equal(payload.contents[0].parts[0].text,messages[0].content);
    assert.equal(payload.contents.at(-1).parts[0].text,'그때 기분은요?');
    assert.equal(payload.generationConfig.temperature,undefined);
    assert.deepEqual(payload.generationConfig.thinkingConfig,{thinkingLevel:'minimal'});
    assert.deepEqual(payload.contents.at(-1).parts[1],{inlineData:{mimeType:'image/jpeg',data:'/9j/2Q=='}});
    assert.equal(payload.contents[0].parts.length,1);
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

test('Gemini permission errors are distinct from invalid keys and never echo upstream text',async()=>{
  const originalFetch=globalThis.fetch,originalKey=process.env.GEMINI_API_KEY;
  process.env.GEMINI_API_KEY='test-only';
  try{
    for(const [status,message,code] of [[403,'Project access restricted test-sensitive-value','permission_denied'],[400,'API key not valid test-sensitive-value','bad_key'],[402,'Payment required test-sensitive-value','billing_required']]){
      globalThis.fetch=async()=>new Response(JSON.stringify({error:{message}}),{status});
      const response=await handler(new Request('https://test.local/api/chat',{method:'POST',body:JSON.stringify({room_id:'donggyu',provider:'gemini',messages:[{role:'user',content:'안녕'}]})}));
      const result=await response.json();assert.equal(result.code,code);assert.ok(!JSON.stringify(result).includes('test-sensitive-value'));
    }
  }finally{globalThis.fetch=originalFetch;if(originalKey===undefined)delete process.env.GEMINI_API_KEY;else process.env.GEMINI_API_KEY=originalKey;}
});

test('invalid or oversized photos are rejected',async()=>{
  for(const image of ['data:text/html;base64,AAAA','data:image/jpeg;base64,'+'A'.repeat(1400000)]){
    const response=await handler(new Request('https://test.local/api/chat',{method:'POST',body:JSON.stringify({room_id:'donggyu',messages:[{role:'user',content:'사진'}],image})}));
    assert.equal(response.status,422);
  }
});

test('oversized history is rejected before calling the provider', async () => {
  const response=await handler(new Request('https://test.local/api/chat',{method:'POST',body:JSON.stringify({room_id:'donggyu',messages:Array.from({length:41},()=>({role:'user',content:'안녕'}))})}));
  assert.equal(response.status,422);
});

test('rooms use a brief greeting and persona UI has no AI label', async () => {
  const response=await handler(new Request('https://test.local/api/rooms'));
  const rooms=await response.json();
  assert.equal(rooms.find(r=>r.id==='donggyu').hello,'');
  assert.deepEqual(rooms.find(r=>r.id==='donggyu').chips,[]);
  for(const path of ['../../Simple Chat bot/frontend/js/ui/rooms.js','../../Simple Chat bot/standalone.html']) {
    const source=fs.readFileSync(new URL(path,import.meta.url),'utf8');
    assert.ok(!source.includes('AI 페르소나'));
    assert.ok(!source.includes('합성 페르소나 데이터로 만든 AI 대화 상대예요'));
  }
});

test('opening a persona room never creates a greeting bubble', () => {
  const source=fs.readFileSync(new URL('../../Simple Chat bot/frontend/js/ui/messages.js',import.meta.url),'utf8');
  const greet=source.match(/export function greetRoom\(R\) \{[^\n]+/)[0].replace('export ','');
  let calls=0;
  const room={def:{kind:'persona',hello:'stale saved greeting'}};
  vm.runInNewContext(greet+'\ngreetRoom(room)',{room,botGroup:()=>{calls++;return {render(){}};}});
  assert.equal(calls,0);
  const html=fs.readFileSync(new URL('../../Simple Chat bot/standalone.html',import.meta.url),'utf8');
  const start=html.indexOf('  function greetRoom(R) {');
  const end=html.indexOf('\n  }',start)+4;
  vm.runInNewContext(html.slice(start,end)+'\ngreetRoom(room)',{room:{def:{persona:true,hello:'stale greeting'}},botGroup:()=>{calls++;return {render(){}};}});
  assert.equal(calls,0);
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
