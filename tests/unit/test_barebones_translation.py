from flask_babel import force_locale

from app.lib.translations import translate_term


def test_barebones_lockpick_item_differs_from_lockpick_hireling(app_with_babel):
    # #given: "Lockpick" names a Barebones item and a Second Edition hireling.
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        hireling, item = translate_term('Lockpick'), translate_term('Lockpick', 'equipment')
    # #then
    assert (hireling, item) == ('Cerrajero', 'Ganzúa')


def test_barebones_form_shows_spanish_tables(app_with_babel):
    # #given: a fresh Barebones creation form.
    from app.blueprints.charcreo_barebones import new_state, render_form
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        html = render_form(new_state())
    # #then: backgrounds, armor, weapons, packages and random rows read in Spanish.
    for text in ('Acólito', 'Ninguna', 'Daga, garrote, hoz, báculo, etc. (d6 de daño)',
                 'Lote de equipo: Guerrero', 'Libro de Hechizos aleatorio'):
        assert text in html
