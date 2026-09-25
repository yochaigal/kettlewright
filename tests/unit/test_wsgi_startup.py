"""Exercise production import order in a fresh process, outside pytest's imports."""
import os
from pathlib import Path
import subprocess
import sys


def test_preloaded_wsgi_patches_before_https_libraries():
    result = subprocess.run(
        [sys.executable, '-c', '''
import warnings
import gunicorn.app.wsgiapp
from gevent.monkey import MonkeyPatchWarning
warnings.simplefilter('error', MonkeyPatchWarning)
from wsgi import application
from gevent import monkey
assert monkey.is_module_patched('ssl')
assert monkey.is_module_patched('socket')
from urllib3.util.ssl_ import create_urllib3_context
import ssl
context = create_urllib3_context()
assert context.minimum_version == ssl.TLSVersion.TLSv1_2
assert context.verify_mode == ssl.CERT_REQUIRED
assert context.check_hostname
assert application is not None
print('production TLS context OK')
'''],
        cwd=Path(__file__).resolve().parents[2],
        env={**os.environ, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
             'USE_FLASK': 'False', 'USE_REDIS': 'False', 'FLASK_DEBUG': '0'},
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'production TLS context OK' in result.stdout
