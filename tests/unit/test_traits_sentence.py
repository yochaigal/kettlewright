from flask_babel import force_locale

from app.lib.char_utils import TraitValue, traits_text

TRAITS = [('Physique', 'Short'), ('Skin', 'Tattooed'), ('Hair', 'Bald'), ('Face', 'Chiseled'),
          ('Speech', 'Cryptic'), ('Clothing', 'Livery'), ('Virtue', 'Tolerant'), ('Vice', 'Nervous')]


def test_spanish_trait_sentence_puts_values_after_their_nouns(app_with_babel):
    # #given: Spanish translates the whole trait sentence.
    traits = [TraitValue(name, value) for name, value in TRAITS]
    with app_with_babel.test_request_context(), force_locale('es'):
        # #when
        text = traits_text('34', traits)
    # #then
    assert text == ('Tu físico es bajo, tu piel tatuada y tu cabello calvo. Tu rostro es cincelado '
                    'y tu voz enigmática. Tu vestimenta es de uniforme. Eres tolerante y nervioso. '
                    'Tienes 34 años.')


def test_untranslated_trait_sentence_keeps_word_by_word_form(app_with_babel):
    # #given: English has no translation for the whole sentence.
    traits = [TraitValue(name, value) for name, value in TRAITS]
    with app_with_babel.test_request_context(), force_locale('en'):
        # #when
        text = traits_text('34', traits)
    # #then
    assert text == ('You have a Short Physique, Tattooed Skin, and Bald Hair. Your Face is Chiseled, '
                    'your Speech Cryptic. You have Livery Clothing. You are Tolerant and Nervous. '
                    'You are 34 years old.')
