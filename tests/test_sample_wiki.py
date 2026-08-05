from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from wiki.core import Page
from wiki.web import create_app


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'create_sample_wiki.py'
spec = spec_from_file_location('create_sample_wiki', SCRIPT)
sample_wiki = module_from_spec(spec)
spec.loader.exec_module(sample_wiki)


def test_create_sample_wiki(tmp_path):
    destination = tmp_path / 'sample'

    created = sample_wiki.create_sample_wiki(destination, page_count=3, seed='test')

    assert (destination / 'config.py').is_file()
    assert len(created) == 4
    assert (destination / 'home.md').read_text(encoding='utf-8').startswith(
        'title: Welcome\n'
    )
    app = create_app(destination)
    with app.test_request_context():
        for path in created:
            page = Page(path, path.stem)
            assert 'sample' in page.tags.split(', ')
