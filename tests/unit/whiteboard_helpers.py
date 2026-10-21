"""Explicit v2 request contexts for the pre-existing drawing/fog regressions."""
BASE = '/party/1/shared-map'


def scene_payload(client, values):
    if not isinstance(values, dict):
        return values
    state = client.get(BASE + '/scene')
    context = {key: state.json[key] for key in ('protocol', 'scene_id', 'activation_version', 'generation')} if state.status_code == 200 else {}
    return {**context, **values}


def post_scene(client, *, json):
    return client.post(BASE + '/scene', json=scene_payload(client, json))


def post_import(client, *, json):
    state = client.get(BASE + '/scene')
    revisions = {key: state.json[key] for key in ('tokens_version', 'markers_version', 'encounter_version')} if state.status_code == 200 else {}
    return client.post(BASE + '/import', json=scene_payload(client, {'mode': 'replace', **revisions, **json}))


def post_fog(client, *, json):
    return client.post(BASE + '/fog', json=scene_payload(client, json))
