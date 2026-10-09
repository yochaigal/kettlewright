# Dependency security

Issue #320 review (2026-10-09): the repository had 68 open Dependabot alerts,
representing 34 advisories duplicated across `Pipfile` and `requirements.txt`.
Both manifests now exclude the affected versions. The files serve different
installation workflows: Docker installs `requirements.txt`, while Pipenv uses
`Pipfile`. Keep the security floors aligned when updating either file.

| Package | Minimum version |
| --- | --- |
| bleach | 6.4.0 |
| Flask | 3.1.3 |
| h11 | 0.16.0 |
| idna | 3.15 |
| Jinja2 | 3.1.6 |
| Mako | 1.3.12 |
| python-dotenv | 1.2.2 |
| python-engineio | 4.13.2 |
| python-socketio | 5.16.2 |
| Werkzeug | 3.1.9 |
| mistune | 3.3.3 |
| pypdf | 6.19.0 |
| PyNaCl | 1.6.2 |

Flask 3.1 also requires Blinker 1.9 or later; the old Pipfile pin was updated.
The Greenlet floor is 3.1.1 so the Pipfile can resolve compatible Gevent wheels.
The audit found additional advisories for the previous minimum versions of
Werkzeug, Mistune, pypdf, and PyNaCl, beyond the repository's current alert list.

Dependabot checks both Python manifests weekly. Audit a freshly installed
application environment, including its transitive dependencies, with:

```sh
python -m pip install pip-audit
python -m pip_audit
```

Also check explicit pins and security floors independently of whatever newer
versions happen to be installed. With Python 3.11 or later:

```sh
python - <<'PY'
import tomllib
from pathlib import Path
packages = tomllib.loads(Path('Pipfile').read_text())['packages']
Path('/tmp/kettlewright-security-floors.txt').write_text('\n'.join(
    name + '==' + version.removeprefix('>=').removeprefix('==')
    for name, version in packages.items() if version != '*'
) + '\n')
PY
python -m pip_audit -r /tmp/kettlewright-security-floors.txt --no-deps --disable-pip
```

The floor audit does not resolve wildcard or transitive dependencies; use both
checks. Both checks returned no known vulnerabilities during this review.
GitHub will reassess repository alerts after these changes reach its default
branch; a local audit does not close alerts on GitHub.
