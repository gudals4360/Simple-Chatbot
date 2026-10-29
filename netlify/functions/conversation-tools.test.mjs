import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {replyParts,deliverReply,createReplyDelivery} from '../../Simple Chat bot/frontend/js/ui/conversation-tools.js';

test('reply bubbles arrive after typing and keep their original order', async()=>{
  const events=[];
  await deliverReply('아 그랬어요?\n\n저도 좀 놀랐어요. 괜찮아요?',{
    typing(){events.push('typing');},sendPart(text){events.push(text);}
  },async ms=>{assert.equal(ms,140);events.push('wait');});
  assert.deepEqual(events,['typing','아 그랬어요?','typing','wait','저도 좀 놀랐어요.','typing','wait','괜찮아요?']);
});

test('Donggyu sends complete sentences while generation is still running',async()=>{
  const events=[];
  const delivery=createReplyDelivery({typing(){},sendPart(text){events.push(text);}},{split:true,wait:async ms=>assert.equal(ms,140)});
  delivery.update('첫 문장이에요. 다음');
  await Promise.resolve();await Promise.resolve();
  assert.deepEqual(events,['첫 문장이에요.']);
  await delivery.finish('첫 문장이에요. 다음 문장이에요.');
  assert.deepEqual(events,['첫 문장이에요.','다음 문장이에요.']);
});

test('other chatbots stream without scheduling any delay',async()=>{
  const events=[];
  const delivery=createReplyDelivery({render(text,done){events.push([text,done]);}},{wait(){throw Error('No delay allowed');}});
  delivery.update('안');delivery.update('안녕하세요');
  assert.deepEqual(events,[['안',false],['안녕하세요',false]]);
  await delivery.finish('안녕하세요');assert.deepEqual(events.at(-1),['안녕하세요',true]);
});

test('long replies split without losing text and empty replies create no bubble',async()=>{
  const text='가'.repeat(250);
  assert.equal(replyParts(text).join(''),text);
  let calls=0;await deliverReply('',{typing(){calls++;},sendPart(){calls++;}});
  assert.equal(calls,0);
});

test('every embedded standalone script parses',()=>{
  const html=fs.readFileSync(new URL('../../Simple Chat bot/standalone.html',import.meta.url),'utf8');
  for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
});

test('long API keys remain intact when switching between masked and multiline inputs',()=>{
  const html=fs.readFileSync(new URL('../../Simple Chat bot/standalone.html',import.meta.url),'utf8');
  const fields={apiKey:{value:''},apiKeyVisible:{value:''},keyCount:{textContent:''}};
  const start=html.indexOf('  function syncKeyInput(source) {');
  const end=html.indexOf('\n  }',start)+4;
  const sync=vm.runInNewContext(html.slice(start,end)+'\nsyncKeyInput',{$:id=>fields[id]});
  const key='sample-authorization-key.'+'x'.repeat(5000)+'+/=';
  fields.apiKey.value=key;sync(fields.apiKey);
  assert.equal(fields.apiKeyVisible.value,key);
  fields.apiKeyVisible.value+='x';sync(fields.apiKeyVisible);
  assert.equal(fields.apiKey.value,key+'x');
  assert.ok(fields.keyCount.textContent.startsWith(String(key.length+1)+'자'));
  for(const id of ['apiKey','apiKeyVisible'])assert.ok(!html.match(new RegExp('<(?:input|textarea) id="'+id+'"[^>]*>'))[0].includes('maxlength'));
});
