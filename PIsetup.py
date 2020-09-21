import PyInstaller.__main__

scriptname = f'ScrapeConferences'

PyInstaller.__main__.run([
    '--clean',
    '--name=%s' % scriptname,
    #'--onedir',
    '--onefile',
    '--windowed',
    '--add-data=syngenta_logo.ico;.',
    #'--add-data=version.txt;.',
    #'--add-binary=%s' % os.path.join('resource', 'path', '*.png'),
    '--icon=%s' % 'syngenta_logo.ico',
    #'--version-file=version.txt',
    #os.path.join('my_package', '__main__.py'),
    'scrape_conferences.py'
])
