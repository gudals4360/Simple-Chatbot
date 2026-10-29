// Shared by the hosted UI and the standalone page.
export function replyParts(text) {
  return text.trim().split(/\n\s*\n|(?<=[.!?。！？])\s+(?=\S)/u).filter(Boolean)
    .flatMap(part => part.length > 100 ? part.match(/.{1,90}(?:\s|$)|.{1,90}/gu) || [part] : [part]);
}

export async function deliverReply(text, group, wait = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  const parts = replyParts(text);
  for (let i = 0; i < parts.length; i++) {
    group.typing();
    await wait(Math.min(3200, 850 + Array.from(parts[i]).length * 45));
    group.sendPart(parts[i]);
  }
}

export function initConversationTools(getRoom, updateSend) {
  const composer = document.getElementById('composer');
  const msg = document.getElementById('msg');
  const shelf = document.createElement('div');
  shelf.className = 'attachment-shelf'; shelf.hidden = true;
  const preview = document.createElement('div'); preview.className = 'photo-draft'; preview.hidden = true;
  const alert = document.createElement('div'); alert.className = 'attachment-alert'; alert.setAttribute('role','status');
  const picker = document.createElement('div'); picker.className = 'emoji-picker'; picker.hidden = true;
  for (const emoji of ['😀','😊','😂','🥹','😍','😎','😭','😅','🤔','👍','👏','🙏','❤️','🔥','🎉','☕','🍚','👋']) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = emoji;
    button.setAttribute('aria-label',emoji+' 넣기');
    button.onclick = () => { msg.setRangeText(emoji,msg.selectionStart,msg.selectionEnd,'end'); msg.dispatchEvent(new Event('input')); msg.focus(); };
    picker.append(button);
  }
  const emojiButton=document.createElement('button'); emojiButton.type='button'; emojiButton.className='icon-btn'; emojiButton.textContent='☺'; emojiButton.setAttribute('aria-label','이모티콘 선택'); emojiButton.setAttribute('aria-expanded','false');
  emojiButton.onclick=()=>{picker.hidden=!picker.hidden;emojiButton.setAttribute('aria-expanded',String(!picker.hidden));shelf.hidden=picker.hidden&&preview.hidden&&!alert.textContent;};
  const photoButton=document.createElement('button'); photoButton.type='button'; photoButton.className='icon-btn'; photoButton.textContent='＋'; photoButton.setAttribute('aria-label','사진 첨부');
  const input=document.createElement('input'); input.type='file'; input.accept='image/jpeg,image/png,image/webp'; input.hidden=true;
  photoButton.onclick=()=>{if(!getRoom()?.busy)input.click();};
  let selection=0;
  input.onchange=async()=>{
    const room=getRoom(), token=++selection, file=input.files[0]; input.value='';
    if(!file||!room||room.busy)return;
    alert.textContent='';
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>10*1024*1024){alert.textContent='JPG·PNG·WebP 사진을 10MB 이하로 선택해 주세요.';shelf.hidden=false;return;}
    try {
      const bitmap=await createImageBitmap(file);
      const scale=Math.min(1,1280/Math.max(bitmap.width,bitmap.height));
      const canvas=document.createElement('canvas'); canvas.width=Math.max(1,Math.round(bitmap.width*scale)); canvas.height=Math.max(1,Math.round(bitmap.height*scale));
      const context=canvas.getContext('2d');context.fillStyle='#fff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
      const image=canvas.toDataURL('image/jpeg',0.78);
      if(image.length>1400000)throw Error('사진 용량이 커요. 더 작은 사진을 선택해 주세요.');
      if(token!==selection||getRoom()!==room)return;
      room.attachment=image; refresh();updateSend();
    }catch(e){alert.textContent=e.message||'사진을 읽지 못했어요.';shelf.hidden=false;}
  };
  function refresh(){
    selection++;preview.replaceChildren(); const image=getRoom()?.attachment;
    preview.hidden=!image;picker.hidden=true;emojiButton.setAttribute('aria-expanded','false');alert.textContent='';
    if(image){const img=document.createElement('img');img.src=image;img.alt='보낼 사진 미리보기';const remove=document.createElement('button');remove.type='button';remove.textContent='사진 삭제';remove.onclick=()=>{getRoom().attachment=null;refresh();updateSend();};preview.append(img,remove);}
    shelf.hidden=preview.hidden;
  }
  shelf.append(preview,picker,alert);composer.before(shelf);composer.prepend(photoButton,emojiButton,input);
  document.addEventListener('keydown',event=>{if(event.key==='Escape'){picker.hidden=true;emojiButton.setAttribute('aria-expanded','false');shelf.hidden=preview.hidden&&!alert.textContent;}});
  return {refresh};
}
