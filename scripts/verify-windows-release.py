"""Verify every release asset before emitting a backwards-compatible update feed."""
import hashlib,json,os,re
from pathlib import Path
import urllib.request,urllib.parse


def validate(value):
 v=value['version'];assert re.fullmatch(r'\d{1,6}\.\d{1,6}\.\d{1,6}',v)
 assert value['preferred'] in ('full','lite') and 'full' in value
 assert value['preferred'] in value
 for kind in ('full','lite'):
  if kind not in value:continue
  a=value[kind];u=urllib.parse.urlsplit(a['url'])
  assert u.scheme=='https' and u.hostname=='release-assets.githubusercontent.com' and not u.username and not u.password
  assert re.fullmatch('[a-f0-9]{64}',a['sha256']) and type(a['size']) is int and 2<a['size']<2*1024**3
  if kind=='lite':assert a['size']<=10*1024**2
 return value


def publish_files(value,repo,fetch=None):
 value=validate(value);v=value['version'];public={}
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):return None
 if fetch is None:fetch=lambda url:urllib.request.build_opener(NoRedirect).open(url,timeout=120)
 for kind in ('full','lite'):
  if kind not in value:continue
  a=value[kind];name=f'JieliuWorkbench-{v}-Windows-x64-'+('Setup' if kind=='full' else 'Update')+'.exe'
  h=hashlib.sha256();size=0
  with fetch(a['url']) as response,open(name,'wb') as output:
   for chunk in iter(lambda:response.read(1024*1024),b''):
    size+=len(chunk)
    if size>a['size']:raise ValueError('Downloaded asset exceeds declared size')
    h.update(chunk);output.write(chunk)
  assert size==a['size'] and h.hexdigest()==a['sha256'],'Release asset checksum mismatch'
  with open(name,'rb') as f:assert f.read(2)==b'MZ','Not a Windows executable'
  Path(name+'.sha256').write_text(a['sha256']+'  '+name+'\n')
  public[kind]={'size':size,'sha256':a['sha256'],'url':f'https://github.com/{repo}/releases/download/v{v}/{name}'}
 chosen=public[value['preferred']]
 manifest={'format':1,'platform':'win32','arch':'x64','version':v,**chosen}
 Path('windows-update.json').write_text(json.dumps(manifest,indent=2))
 Path('windows-distribution.json').write_text(json.dumps({'version':v,'preferred':value['preferred'],**public},indent=2))
 print(json.dumps({'verified':True,'version':v,'preferred':value['preferred'],'assets':{k:a['size'] for k,a in public.items()}}))
 return manifest

if __name__=='__main__':
 value=json.loads(os.environ['ARTIFACTS_JSON'])
 for k in ('full','lite'):
  if k in value:print('::add-mask::'+value[k]['url'])
 publish_files(value,os.environ['GH_REPO'])
