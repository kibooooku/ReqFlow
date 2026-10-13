"""Capture actual source files and hashes before review; never manufacture history."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib,json,sys
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
label=sys.argv[1] if len(sys.argv)>1 else 'initial'
out=root/'evidence'/label
out.mkdir(parents=True,exist_ok=True)
entries=[]
with ZipFile(out/'source.zip','w',ZIP_DEFLATED) as z:
    for folder in ('app','tests','scripts','docs'):
        for p in sorted((root/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                rel=p.relative_to(root).as_posix(); data=p.read_bytes()
                z.writestr(rel,data); entries.append({'path':rel,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    for name in ('requirements.txt','requirements.lock','run.ps1','run.bat','.gitignore','README.md'):
        p=root/name
        if p.exists():
            data=p.read_bytes(); z.writestr(name,data)
            entries.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(out/'source-manifest.json').write_text(json.dumps({'label':label,'captured_at':datetime.now(timezone.utc).isoformat(),'files':entries},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Captured {len(entries)} files: {label}')
