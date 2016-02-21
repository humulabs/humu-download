"""
Usage: humu-download [options] EXPORT-FILE
       humu-download -h

Download Humu data files for a subject table export.

Arguments:
  EXPORT-FILE   Humu subject export CSV file

Options:
  -c --chunk-size=CHUNK-SIZE   number of bytes to process at a
                               time [default: 4096]
  -d --dest-dir=DEST-DIR       download destination directory. By default
                               a subdir of the current directory
                               named after the CSV file is used. The directory
                               is created if it does not exist. Any existing
                               data files in the directory are overwritten.
  -h --help                    show help
  -v --version                 show version
"""
import docopt
import requests
import urwid
from urwid_timed_progress import TimedProgressBar
import csv
import os
from . import __version__


class App(object):
    def __init__(self, files, dest_dir, chunk_size):
        self.files = [f for f in files if f.get('url')]
        self.dest_dir = dest_dir
        self.chunk_size = chunk_size

        palette = [
            ('normal', 'white', 'black', 'standout'),
            ('complete', 'white', 'dark magenta'),
            ('footer',   'white', 'dark gray'),
            ]

        units = [
            ('bytes', 1),
            ('kB', 1000),
            ('MB', 1000000),
            ('GB', 1000000000)]

        self.file_progress = TimedProgressBar('normal',
                                              'complete',
                                              label='Current File',
                                              label_width=15,
                                              units=units,
                                              done=1)

        self.overall_progress = TimedProgressBar('normal',
                                                 'complete',
                                                 label='Overall',
                                                 label_width=15,
                                                 units=units,
                                                 done=1)

        self._status = urwid.Text('')

        progress = urwid.LineBox(urwid.Pile([
            ('pack', self.file_progress),
            ('pack', urwid.Divider()),
            ('pack', self.overall_progress)]))

        self.footer = urwid.Text('Ctrl-C to abort')
        main_view = urwid.Frame(urwid.ListBox([
            progress,
            urwid.Divider(),
            self._status]),
            footer=urwid.AttrWrap(self.footer, 'footer'))

        def keypress(key):
            if key in ('q', 'Q'):
                raise urwid.ExitMainLoop()
        self.loop = urwid.MainLoop(main_view,
                                   palette,
                                   unhandled_input=keypress)

    def status(self, msg):
        self._status.set_text(msg)
        self.loop.draw_screen()

    def run(self):
        self.loop.set_alarm_in(0.1, self.download_files)
        self.loop.run()

    def download_files(self, *args, **kwargs):
        self.overall_progress.done = sum([f['size'] for f in self.files])
        self.status('starting download ...')
        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)

        for f in self.files:
            self.download_file(f)
        self.files = []
        self.footer.set_text('q to exit')
        self.status('download complete')

    def download_file(self, file):
        filename = os.path.join(self.dest_dir, file['name'])
        self.status('downloading {} ...'.format(filename))
        r = requests.get(file['url'], stream=True)

        estimated_size = file['size']
        actual_size = int(r.headers.get('content-length', 0))
        if actual_size != estimated_size:
            done = self.overall_progress.done + actual_size - estimated_size
            self.overall_progress.add_progress(0, done=done)

        with open(filename, 'wb') as f:
            self.file_progress.reset()
            self.file_progress.done = actual_size
            self.loop.draw_screen()

            for chunk in r.iter_content(self.chunk_size):
                f.write(chunk)
                num_bytes = len(chunk)
                self.file_progress.add_progress(num_bytes)
                self.overall_progress.add_progress(num_bytes)
                self.loop.draw_screen()


def main():
    args = docopt.docopt(__doc__,
                         version='humu-download {}'.format(__version__))
    csv_file = args['EXPORT-FILE']

    dest_dir = args.get('--dest-dir')
    if not dest_dir:
        dest_dir = os.path.splitext(os.path.basename(csv_file))[0]

    with open(csv_file, 'r') as f:
        lines = (line for line in f if not line.lstrip().startswith('#'))
        reader = csv.DictReader(lines)
        files = []
        for row in reader:
            for key in row.keys():
                if key.endswith('_url'):
                    ds = key.rsplit('_', 1)[0]
                    url = row[key]
                    if url:
                        size = row['{}_size'.format(ds)]
                        if size:
                            size = int(size)
                        else:
                            size = 0
                        name = '{}-{}-{}'.format(row['ID'], row['_id'], ds)
                        files.append({'name': name, 'url': url, 'size': size})

        app = App(files, dest_dir, int(args['--chunk-size']))
        app.run()


if __name__ == '__main__':
    exit(main())
