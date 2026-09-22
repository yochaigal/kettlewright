from app.lib.item_description import render_item_description


def test_markdown_image_and_text_render_together():
    result = str(render_item_description('A strange book.\n![Cover](https://example.org/cover.png)'))
    assert 'A strange book.<br>' in result
    assert 'src="https://example.org/cover.png"' in result
    assert 'alt="Cover"' in result
    assert 'referrerpolicy="no-referrer"' in result


def test_description_strips_active_html_and_unsafe_sources():
    result = str(render_item_description('<img src="javascript:alert(1)" onerror="bad()"><script>bad()</script>'))
    assert 'javascript:' not in result
    assert 'onerror' not in result
    assert '<script' not in result
    assert '<img' not in str(render_item_description('![bad](data:text/html,payload)'))


def test_html_image_and_existing_formatting_remain_supported():
    result = str(render_item_description('<b>Book</b> <img src="https://example.org/a.png" alt="Glyph">'))
    assert '<b>Book</b>' in result
    assert 'alt="Glyph"' in result
