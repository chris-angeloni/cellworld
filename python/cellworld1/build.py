import sys
from easy_pack import EasyPackModule
import os

module = EasyPackModule.read('.')
if not os.path.exists('setup/setup.py') or os.path.getctime('__info__.py') > os.path.getctime('setup/setup.py'):
	print('package info file has changed, rebuilding setup')
	module.create_setup_files('../setup')
build = module.build_module('python-build')
if build:
	print(f'build succeeded: {build}')
	if '-upload' in sys.argv:
		import os
		username = ""
		if '-user' in sys.argv:
			username = sys.argv[sys.argv.index('-user')+1]
		password = ""
		if '-password' in sys.argv:
			password = sys.argv[sys.argv.index('-password')+1]
		repository = ""
		if '-repository' in sys.argv:
			repository = sys.argv[sys.argv.index('-repository')+1]
		os.system('cd ' + build + '; twine upload dist/*' + ((' --repository-url  ' + repository) if repository else '') + ((' -u ' + username) if username else '') + ((' -p ' + password) if password else ''))
	else:
		print('use twine upload --repository-url [pypi-repository-url] dist/* to upload the package')
	if '-install' in sys.argv:
		os.system(f'pip install ./{build}')
	module.save('.')
else:
	print('build failed')
