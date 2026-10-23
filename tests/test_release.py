import contextlib,hashlib,importlib.util,io,json,os,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('release',Path(__file__).resolve().parents[1]/'scripts/verify-windows-release.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
class ReleaseTests(unittest.TestCase):
 def value(self):
  data=b'MZtest'
  asset={'url':'https://release-assets.githubusercontent.com/test','sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
  return {'version':'0.11.8','preferred':'lite','full':asset.copy(),'lite':asset.copy()}
 def test_both_checked_and_small_selected_with_original_format(self):
  with tempfile.TemporaryDirectory() as tmp:
   old=os.getcwd();os.chdir(tmp)
   try:
    value=self.value();manifest=release.publish_files(value,'owner/repo',lambda u:io.BytesIO(b'MZtest'))
    self.assertEqual(manifest['format'],1);self.assertTrue(manifest['url'].endswith('-Update.exe'))
    self.assertTrue(Path('JieliuWorkbench-0.11.8-Windows-x64-Setup.exe').exists())
   finally:os.chdir(old)
 def test_changed_runtime_full_selection(self):
  value=self.value();value.pop('lite');value['preferred']='full'
  self.assertEqual(release.validate(value)['preferred'],'full')
 def test_invalid_source_size_hash_or_missing_full_rejected(self):
  for change in ('size','host','full'):
   value=self.value()
   if change=='size':value['lite']['size']=11*1024**2
   if change=='host':value['full']['url']='https://evil.test/a'
   if change=='full':value.pop('full')
   with self.assertRaises(AssertionError):release.validate(value)
 def test_corrupt_full_or_light_cannot_emit_feed(self):
  for kind in ('full','lite'):
   with tempfile.TemporaryDirectory() as tmp:
    old=os.getcwd();os.chdir(tmp)
    try:
     value=self.value();value[kind]['sha256']='0'*64
     with self.assertRaises(AssertionError):release.publish_files(value,'owner/repo',lambda u:io.BytesIO(b'MZtest'))
     self.assertFalse(Path('windows-update.json').exists())
    finally:os.chdir(old)
