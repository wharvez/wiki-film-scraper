import os, inspect, sys, time
from datetime import timedelta

tests_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
project_dir = os.path.dirname(tests_dir)
src_dir = os.path.join(project_dir, 'src')
wfs_dir = os.path.join(src_dir, 'wfs')
sys.path[0:0] = [src_dir, wfs_dir]

from wfs import Scraper


def main(choices_options):
    choices_main = []
    for i in range(len(choices_options) or 1):
        choices_main.append(choices_options[i])

        start_time = time.monotonic()

        test_scraper = Scraper(choices_input=choices_main, html_from_file=True)
        test_scraper.set_films()
        for film in test_scraper.films:
            print(getattr(film, 'basis', f'NO BASIS FOR {film.titles[0].detail}'))
        test_scraper.save_films()

        end_time = time.monotonic()
        delta = timedelta(seconds=end_time - start_time)
        print(f'Program Execution Time for n={len(test_scraper.choices)}: {delta.total_seconds()} seconds')


test_choices_options = [
    'scarlet street',
    'caged',
    'la nuit du carrefour'
]
main(test_choices_options)
