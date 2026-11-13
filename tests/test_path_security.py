import os

import pytest

from wiki.core import Wiki
from wiki.web import create_app


CONTENT = 'title: Outside\ntags: test\n\nOutside sentinel\n'


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / 'content'
    root.mkdir()
    outside = tmp_path / 'outside.md'
    outside.write_text(CONTENT, encoding='utf-8')
    return Wiki(str(root)), root, outside


@pytest.mark.parametrize('method', ['path', 'exists', 'get', 'get_or_404', 'get_bare', 'delete'])
@pytest.mark.parametrize('url', ['../outside', 'nested/../../outside', '../content-evil/page'])
def test_escape_rejected(sandbox, method, url):
    wiki, root, outside = sandbox
    (root / 'nested').mkdir()
    with pytest.raises(RuntimeError):
        getattr(wiki, method)(url)
    assert outside.read_text(encoding='utf-8') == CONTENT


def test_absolute_escape_rejected(sandbox):
    wiki, _, outside = sandbox
    with pytest.raises(RuntimeError):
        wiki.get(str(outside.with_suffix('')))


@pytest.mark.parametrize('source,destination', [('inside', '../content-evil/page'), ('../outside', 'inside')])
def test_move_checks_both_paths(sandbox, source, destination):
    wiki, root, outside = sandbox
    (root / 'inside.md').write_text(CONTENT, encoding='utf-8')
    with pytest.raises(RuntimeError):
        wiki.move(source, destination)
    assert outside.read_text(encoding='utf-8') == CONTENT
    assert (root / 'inside.md').exists()
    assert not (root.parent / 'content-evil').exists()


def make_link(link, target):
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError) as error:
        pytest.skip('Symbolic links unavailable: %s' % error)


@pytest.mark.parametrize('method', ['get', 'get_bare', 'delete'])
def test_file_symlink_escape(sandbox, method):
    wiki, root, outside = sandbox
    make_link(root / 'link.md', outside)
    with pytest.raises(RuntimeError):
        getattr(wiki, method)('link')
    assert outside.read_text(encoding='utf-8') == CONTENT


def test_directory_symlink_escape(sandbox):
    wiki, root, outside = sandbox
    make_link(root / 'linked', root.parent)
    with pytest.raises(RuntimeError):
        wiki.get_bare('linked/new')
    assert not (outside.parent / 'new.md').exists()


def test_inside_symlink_keeps_normal_behavior(sandbox):
    wiki, root, _ = sandbox
    target = root / 'actual.md'
    target.write_text(CONTENT, encoding='utf-8')
    make_link(root / 'alias.md', target)
    assert wiki.get('alias').title == 'Outside'
    assert wiki.delete('alias')
    assert target.read_text(encoding='utf-8') == CONTENT


def test_symlink_root_is_supported(sandbox):
    _, root, _ = sandbox
    alias = root.parent / 'root-alias'
    make_link(alias, root)
    wiki = Wiki(str(alias))
    page = wiki.get_bare('normal')
    page.title = 'Normal'
    page.body = 'Body'
    page.save()
    assert wiki.get('normal').title == 'Normal'


def test_symlink_parent_traversal_uses_real_location(sandbox):
    wiki, root, outside = sandbox
    nested = root / 'nested'
    nested.mkdir()
    make_link(root / 'linked', root.parent)
    with pytest.raises(RuntimeError):
        wiki.path('linked/../' + root.parent.name + '/outside')
    assert outside.read_text(encoding='utf-8') == CONTENT


def test_index_does_not_read_outside_symlinks(sandbox):
    wiki, root, outside = sandbox
    make_link(root / 'link.md', outside)
    assert wiki.index() == []


def test_normal_lifecycle_with_relative_root(sandbox):
    _, root, _ = sandbox
    wiki = Wiki(os.path.relpath(root))
    page = wiki.get_bare('nested/hello')
    page.title = 'Hello'
    page.body = 'Local body'
    page.save()
    assert wiki.get('nested/hello').body == 'Local body'
    assert wiki.move('nested/hello', 'Other/Page') == 'other/page'
    assert wiki.get('other/page').title == 'Hello'
    assert wiki.delete('other/page')


@pytest.mark.parametrize('method,path', [
    ('get', '/nested/../../outside/'),
    ('get', '/delete/../outside/'),
    ('post', '/edit/../outside/'),
    ('post', '/edit/../new/'),
    ('get', '/delete/%2e%2e/outside/'),
])
def test_web_escape_has_no_side_effects(sandbox, method, path):
    _, root, outside = sandbox
    (root / 'nested').mkdir()
    (root / 'config.py').write_text("PRIVATE=False\nSECRET_KEY='test'\n", encoding='utf-8')
    app = create_app(str(root))
    # Model a public client with a valid form; CSRF is tested separately by Flask-WTF.
    app.config.update(WTF_CSRF_ENABLED=False, PROPAGATE_EXCEPTIONS=False)
    response = getattr(app.test_client(), method)(path, data={'title': 'Changed', 'body': 'Changed'})
    assert response.status_code in (400, 403, 404, 500)
    assert outside.read_text(encoding='utf-8') == CONTENT
    assert not (root.parent / 'new.md').exists()
