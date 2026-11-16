/** Keep the output name stable while an OpenFilm canvas request has no locally delivered result. */
export interface CanvasMediaRequest { verb: string; args: Record<string, unknown> }
type Store = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
const stable = (value: unknown) => JSON.stringify(value, (_key, item) => item && typeof item === 'object' && !Array.isArray(item)
  ? Object.fromEntries(Object.keys(item).sort().map(key => [key,item[key]])) : item);
async function hash(value: unknown) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(stable(value))))).map(byte => byte.toString(16).padStart(2,'0')).join('');
}
export async function pendingCanvasMedia(scope: unknown, request: CanvasMediaRequest, pick: {via?:string;model?:string}, storage: Store = localStorage) {
  const id = 'openfilm:canvas-media-pending:v1:' + await hash(scope);
  const {out: proposed,...args} = request.args;
  const identity = await hash({verb:request.verb,args,pick});
  let raw: string | null;
  try { raw = storage.getItem(id); } catch { throw new Error('Could not read the saved media request. No new generation was started.'); }
  let previous: {identity:string;out:string;operation?:string} | null = null;
  if (raw !== null) {
    try {
      previous = JSON.parse(raw);
      if (!previous || !/^[a-f0-9]{64}$/.test(previous.identity) || typeof previous.out !== 'string' || !previous.out || previous.out.length > 512) throw Error();
    } catch { throw new Error('The saved canvas media request is damaged. Check its outcome before generating another take.'); }
  }
  const resumed = previous?.identity === identity;
  const out = resumed ? previous!.out : proposed;
  if (typeof out !== 'string' || !out) throw new Error('A generated output name is required.');
  const operation = resumed && previous?.operation || crypto.randomUUID();
  const saved = JSON.stringify({identity,out,operation});
  try { storage.setItem(id,saved); } catch { throw new Error('Could not save the media recovery request. No new generation was started.'); }
  return {request:{...request,args:{...request.args,out}},operation,resumed,
    finish() { try { if (storage.getItem(id) === saved) storage.removeItem(id); } catch { /* the delivered asset is already saved */ } },
  };
}

/** Resume the unfinished positions of a batch; already delivered takes must not be paid for again. */
export async function pendingMediaBatch(scope:unknown,request:CanvasMediaRequest,pick:{via?:string;model?:string},count:number,storage:Store=localStorage) {
  const {out:_,...args}=request.args;
  const id='openfilm:media-batch:v1:'+await hash(scope),identity=await hash({verb:request.verb,args,pick,count});
  let row:{identity:string;completed:number}|null=null;
  try {const raw=storage.getItem(id);if(raw){row=JSON.parse(raw);if(!row||typeof row.identity!=='string'||!Number.isInteger(row.completed)||row.completed<0||row.completed>count)throw Error();}}
  catch {throw new Error('The saved media batch cannot be read. Check its original results before creating more takes.');}
  let completed=row?.identity===identity?row.completed:0;
  const save=()=>{storage.setItem(id,JSON.stringify({identity,completed}));};
  save();
  return {completed,advance(next:number){completed=next;save();},finish(){storage.removeItem(id);}};
}
