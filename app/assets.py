from flask_assets import Bundle, Environment
import sys


def compile_static_assets(app):
    assets = Environment(app)
    assets.auto_build = True
    assets.debug = app.config['DEBUG']

    # Ensure cache is always enabled, but set to False in debug mode
    assets.cache = True
    assets.manifest = 'file'  # Use file-based manifest

    if app.config['DEBUG']:
        assets.cache = False
        assets.manifest = False  # Disable manifest in debug mode

    scss = Bundle('src/scss/magic.css/normalize.css', 'src/scss/magic.css/magick.css',
                  'src/scss/main.scss', 'src/scss/modals.scss', 'src/scss/inventory.scss',
                  'src/scss/create.scss', 'src/scss/character.scss', 'src/scss/characters-parties.scss', 'src/scss/party.scss',
                  filters='libsass',
                  output='dist/css/style.css',
                  depends=('**/*.scss'))

    assets.register('scss_all', scss)

    if app.config['DEBUG']:
        print('Compiling static assets in debug mode', file=sys.stderr)
        try:
            scss.build(force=True)
            print('Assets compiled successfully', file=sys.stderr)
        except Exception as e:
            print(f'Error compiling assets: {e}', file=sys.stderr)
    else:
        scss.build()

    return assets
