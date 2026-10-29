import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {replyParts,deliverReply} from '../../Simple Chat bot/frontend/js/ui/conversation-tools.js';

test('reply bubbles arrive after typing and keep their original order', async()=>{
  const events=[];
  await deliverReply('아 그랬어요?\n\n저도 좀 놀랐어요. 괜찮아요?',{
    typing(){events.push('typing');},sendPart(text){events.push(text);}
  },async ms=>{assert.ok(ms>=850&&ms<=3200);events.push('wait');});
  assert.deepEqual(events,['typing','wait','아 그랬어요?','typing','wait','저도 좀 놀랐어요.','typing','wait','괜찮아요?']);
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
