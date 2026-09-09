import fcntl, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('updater',Path(__file__).with_name('auto_update.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
class UpdateSafetyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def options(self):return SimpleNamespace(root=self.root,source=self.root/'source',java=self.root/'java',institution=self.root/'institution')
 def test_path_escape(self):
  with self.assertRaises(ValueError):u.contained(self.root,'../outside')
  (self.root/'link').symlink_to('/tmp')
  with self.assertRaises(ValueError):u.contained(self.root,'link/outside')
 def test_configuration_has_no_temporary_template_dependency(self):
  previous=self.root/'previous';candidate=self.root/'candidate'
  (candidate/'conf').mkdir(parents=True)
  (candidate/'conf/ddmd.properties').write_text('ykiho=00000000\nbackup.month=5\ncompatibility.dmd.dir='+str(previous/'sam/in')+'\n')
  u.configure(candidate,previous)
  text=(candidate/'conf/ddmd.properties').read_text()
  self.assertIn('backup.month=5',text)
  self.assertIn('driver.class.name=IsolatedJdbc',text)
  self.assertNotIn(str(previous),text)
  self.assertIn(str(candidate/'data/tbjcc010.db'),(candidate/'conf/SqlMapConfig.properties').read_text())
 def test_corrupt_payload_rejected_before_stage(self):
  (self.root/'parts').mkdir();p=self.root/'parts/a';p.write_bytes(b'damaged')
  (self.root/'response.tsv').write_text('module\t1\tlib\t01\tm.jar\t'+str(p)+'\tUI\t\n')
  with self.assertRaisesRegex(ValueError,'checksum'):u.payloads(self.root)
 def test_digest_accepts_original_unpadded_representation(self):
  (self.root/'parts').mkdir();p=self.root/'parts/a';p.write_bytes(b'valid')
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  (self.root/'response.tsv').write_text('module\t1\tlib\t'+h+'\tm.jar\t'+str(p)+'\tUI\t\n')
  self.assertEqual(len(u.payloads(self.root)),1)
 def test_pending_report_is_not_resent(self):
  p=self.root/'hira-live-auth-pending';p.mkdir();(p/'pending.dat').write_bytes(b'receipt')
  with patch.object(u,'transport') as send:
   with self.assertRaisesRegex(RuntimeError,'pending'):u.run(self.options())
   send.assert_not_called()
 def test_concurrent_update_is_refused(self):
  with (self.root/'update.lock').open('w') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):u.run(self.options())
 def test_no_update_does_not_apply_or_launch(self):
  def respond(work,*args):(work/'response.tsv').write_text('')
  with patch.object(u,'prepare_transport',return_value={}),patch.object(u,'modules'),patch.object(u,'transport',side_effect=respond),patch.object(u,'apply') as apply,patch.object(u,'launch') as launch:
   u.run(self.options());apply.assert_not_called();launch.assert_not_called()
   self.assertFalse((self.root/'active.json').exists())
 def test_failed_apply_preserves_active_and_reopens_previous(self):
  previous=self.root/'previous';previous.mkdir()
  before={'home':str(previous),'bundleId':'local.test'}
  u.atomic_json(self.root/'active.json',before)
  def download(work,*args):(work/'response.tsv').write_text('update present')
  def copy(source,target,**kwargs):target.mkdir()
  with patch.object(u,'prepare_transport',return_value={}),patch.object(u,'modules'),patch.object(u,'transport',side_effect=download),patch.object(u,'payloads',return_value=[['module']]),patch.object(u.shutil,'copytree',side_effect=copy),patch.object(u,'configure'),patch.object(u,'stage'),patch.object(u,'stop_owned',return_value=True),patch.object(u,'apply',side_effect=RuntimeError('injected apply failure')),patch.object(u,'checked') as command:
   with self.assertRaisesRegex(RuntimeError,'injected'):u.run(self.options())
   self.assertEqual(json.loads((self.root/'active.json').read_text()),before)
   command.assert_called_once_with(['open','-n',previous/'DDMD Computer Use.app'])
if __name__=='__main__':unittest.main()
