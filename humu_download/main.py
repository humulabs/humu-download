"""
Usage: humu-download [options] EXPORT-FILE
       humu-download -h

Download Humu data files from a subject table export into CSV data files.

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
  --keep-raw                   keep raw data files in addition to CSV
  -h --help                    show help
  -v --version                 show version
"""
import docopt
import requests
import pandas
import urwid
from urwid_timed_progress import TimedProgressBar
import csv
import os
from . import __version__


class App(object):
    def __init__(self, files, dest_dir, chunk_size, keep_raw):
        self.files = [f for f in files if f.get('url')]
        self.dest_dir = dest_dir
        self.chunk_size = chunk_size
        self.keep_raw = keep_raw

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
        done = sum([f['size'] for f in self.files])
        if done != 0:
            self.overall_progress.done = done
        self.status('starting download ...')
        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)

        for f in self.files:
            self.download_file(f)

        self.status('download complete')
        self.convert_files()

    def download_file(self, file):
        file['hdf'] = os.path.join(self.dest_dir, file['name'])
        self.status('downloading {} ...'.format(file['hdf']))
        r = requests.get(file['url'], stream=True)

        try:
            r.raise_for_status()
        except:
            return False

        estimated_size = file['size']

        file['actual_size'] = int(r.headers.get('content-length', 0))
        if file['actual_size'] != estimated_size:
            overall_done = (self.overall_progress.done +
                            file['actual_size'] - estimated_size)
            if done != 0:
                self.overall_progress.add_progress(0, done=done)

        if file['actual_size'] != 0:
            with open(file['hdf'], 'wb') as f:
                self.file_progress.reset()
                self.file_progress.done = file['actual_size']
                self.loop.draw_screen()

                for chunk in r.iter_content(self.chunk_size):
                    f.write(chunk)
                    num_bytes = len(chunk)
                    self.file_progress.add_progress(num_bytes)
                    self.overall_progress.add_progress(num_bytes)
                    self.loop.draw_screen()

        file['download_complete'] = True
        return True

    def convert_files(self):
        files = [f for f in self.files if f.get('download_complete')]
        done = sum([f['actual_size'] for f in files])
        if done != 0:
            self.overall_progress.done = done
        self.status('converting data files to CSV')

        for f in files:
            self.convert_file(f)

        failures = [f for f in self.files if not f.get('success')]
        if failures:
            self.status('Could not process the following files,' +
                        ' please re-export your data and try again:\n  ' +
                        '\n  '.join(f['name'] for f in failures))
        else:
            self.status('complete')
        self.footer.set_text('q to exit')

    def convert_file(self, file):
        self.status('converting {} to CSV'.format(file['hdf']))
        try:
            df = pandas.read_hdf(file['hdf'], 'data')
            file['csv'] = '{}.csv'.format(
                os.path.join(self.dest_dir, file['name']))
            df.to_csv(file['csv'],
                      header=[file['data_series_name']],
                      encoding='utf-8',
                      index_label='datetime')
            file['success'] = True
            if not self.keep_raw:
                os.remove(file['hdf'])
        except Exception as e:
            file['success'] = False

        return file['success']


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
                        files.append({
                            'data_series_name': ds,
                            'name': name,
                            'url': url,
                            'size': size})

        app = App(files,
                  dest_dir,
                  int(args['--chunk-size']),
                  args['--keep-raw'])
        app.run()


if __name__ == '__main__':
    exit(main())
