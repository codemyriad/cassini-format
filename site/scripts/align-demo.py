#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Map independently recognized Scribe words to a checked spoken script.

Multiword numbers retain one recognized spelling and acoustic interval. Punctuation
and conventional text spelling come from the script. No word interval is split,
interpolated or extended. Only explicitly enumerated lexical variants are allowed;
unexpected omissions, repetitions or changed words fail with a useful diff.
"""
import argparse,json,pathlib,re,difflib,sys
ROOT=None
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'static/demo/repair-cafe.script.json'
NUMBERS={'0':'zero','1':'one','2':'two','3':'three','4':'four','5':'five','10':'ten','11':'eleven','12':'twelve','15':'fifteen'}
def normalized_tokens(text,*,allow_clear_variant=False):
    text=text.lower().replace('’',"'").replace('neighbourhood','neighborhood')
    text=re.sub(r'\bmm-hm\b','mm-hmm',text)
    text=re.sub(r'\b(\d+):00\b',r'\1',text)
    text=re.sub(r'\b11:15\b','eleven fifteen',text)
    text=re.sub(r'\d+',lambda m:NUMBERS.get(m[0],m[0]),text)
    if allow_clear_variant:text=re.sub(r'\bcleared\b','clear',text)
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?",text)
def align(sid,turns):
    result=json.loads((ROOT/f'{sid}.scribe.json').read_text())
    source=[];recognized=[];source_tokens=[];recognized_tokens=[]
    allow_clear_variant=sid=='i01'
    for ti,turn in enumerate(turns):
      for text in turn['text'].split():
        tokens=normalized_tokens(text,allow_clear_variant=allow_clear_variant)
        source.append({'text':text,'turn':ti,'lo':len(source_tokens),'hi':len(source_tokens)+len(tokens)})
        source_tokens.extend(tokens)
    for w in result['words']:
      if w['type']!='word':continue
      tokens=normalized_tokens(w['text'],allow_clear_variant=allow_clear_variant)
      recognized.append({**w,'lo':len(recognized_tokens),'hi':len(recognized_tokens)+len(tokens)})
      recognized_tokens.extend(tokens)
    if source_tokens!=recognized_tokens:
      diff=[{'operation':tag,'expected':source_tokens[a:b],'recognized':recognized_tokens[c:d]} for tag,a,b,c,d in difflib.SequenceMatcher(None,source_tokens,recognized_tokens,autojunk=False).get_opcodes() if tag!='equal']
      raise ValueError(f'{sid}: script differs from ASR: {diff}')
    output=[{**t,'words':[]} for t in turns]
    variants=[]
    for w in recognized:
      matching=[s for s in source if s['lo']<w['hi'] and s['hi']>w['lo']]
      if not matching:raise ValueError(f'No scripted token for {w}')
      if matching[0]['lo']!=w['lo'] or matching[-1]['hi']!=w['hi']:
        raise ValueError(f'ASR split a script word: {matching} / {w}')
      if len(set(s['turn'] for s in matching))!=1:raise ValueError('ASR word crosses turn boundary')
      original=' '.join(s['text'] for s in matching)
      prefix=re.match(r'^[^A-Za-z0-9]*',matching[0]['text'])[0]
      suffix=re.search(r'[^A-Za-z0-9]*$',matching[-1]['text'])[0]
      core=re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$','',w['text'])
      if (len(matching)>1 and re.search(r'\d',w['text'])) or (sid=='i03' and core.lower()=='mm-hmm') or (sid=='i01' and core.lower()=='cleared'):
        written=prefix+core+suffix
      elif len(matching)==1:
        written=matching[0]['text']
      else:
        raise ValueError(f'Unexpected merged words {matching} / {w}')
      if written!=original:variants.append({'script':original,'transcript':written,'start':w['start'],'end':w['end']})
      output[matching[0]['turn']]['words'].append({'text':written,'start':w['start'],'end':w['end']})
    for turn in output:
      turn['text']=' '.join(w['text'] for w in turn['words'])
      if not turn['words']:raise ValueError('Empty turn')
    aligned={'turns':output,'evidence':{'provider':'ElevenLabs','model':'scribe_v2','source':f'{sid}.scribe.json','method':'Independent speech recognition; complete normalized lexical match to script, ASR word intervals retained intact. Script punctuation restored.','normalizations':variants,'sourceTokenCount':len(source_tokens),'recognizedTokenCount':len(recognized_tokens),'allowedLexicalVariants':['i01 context-only final clear/cleared'] if allow_clear_variant else []}}
    (ROOT/f'{sid}.aligned.json').write_text(json.dumps(aligned,indent=2,ensure_ascii=False)+'\n')
    print(sid,'turns',len(output),'words',sum(len(t['words']) for t in output),'variants',json.dumps(variants),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache',type=pathlib.Path,required=True)
    ROOT=ap.parse_args().cache
    script=json.loads(SCRIPT.read_text())
    interjections={i['id']:i for s in script['scenes'] for t in s['turns'] for i in t.get('interjections',[])}
    speaker_by_voice={s['voiceId']:s['id'] for s in script['speakers']}
    for scene in script['scenes']:
      align(scene['id'],[{k:t[k] for k in ('id','speaker','text')} for t in scene['turns']])
    for iid,interj in interjections.items():
      request=json.loads((ROOT/f'{iid}.request.json').read_text())
      turns=[{'id':iid if n==1 else f'{iid}-context-{n}','speaker':speaker_by_voice[t['voice_id']],'text':t['text']} for n,t in enumerate(request['inputs'])]
      align(iid,turns)
