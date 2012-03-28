import os
import re
import sublime
import sublime_plugin
import platform
from statusprocess import *
from asyncprocess import *

RESULT_VIEW_NAME = 'csslint_result_view'
SETTINGS_FILE    = "CSSLint.sublime-settings"

if sublime.arch() == 'windows':
	FOLDER_MARKER = '\\'
else:
	FOLDER_MARKER = '/'

class CsslintCommand(sublime_plugin.WindowCommand):  
	def run(self, paths = False):  
		settings        = sublime.load_settings('SETTINGS_FILE')
		file_path       = None
		file_paths      = None
		self.file_paths = None
		cssFiles        = []
		
		def add_css_to_list(path):
			if path.endswith('.css'):
				cssFiles.append('"' + path + '"')

		# Lint path(s) (sidebar context menu)
		if paths != False:
			# Walk through any directories and make a list of css files
			
			for path in paths:
				if os.path.isdir(path) == True:
					for path, subdirs, files in os.walk(path):
					    for name in files:
							add_css_to_list(os.path.join(path, name))

				else:
					add_css_to_list(path)

			# Generate the command line paths argument
			if len(cssFiles) < 1:
				sublime.error_message("No CSS files selected.")
				return
			else:
				self.file_paths = cssFiles
				file_paths      = ' '.join(cssFiles)
		
		# Lint current file
		else:
			if self.window.active_view().file_name() == None:
				sublime.error_message("Please save your file before running CSSLint.")
				return

			file_path = '"' + self.window.active_view().file_name() + '"'
		
		file_name               = os.path.basename(file_path) if file_path else ', '.join(self.file_paths)
		self.buffered_data      = ''
		self.file_path          = file_path
		self.file_name          = file_name
		path_argument           = file_paths if file_paths else file_path
		self.is_running         = True
		self.tests_panel_showed = False

		init_tests_panel(self)
		
		# create the csslint command for node
		# cmd = 'csslint' + ' --format=compact ' + " '" + file_path.encode('utf-8') + "'"

		rhino_path = settings.get('rhino_path', '"' + sublime.packages_path() + '/CSSLint/scripts/rhino/js.jar' + '"')
		csslint_rhino_js = settings.get('csslint_rhino_js', '"' + sublime.packages_path() + '/CSSLint/scripts/csslint/csslint-rhino.js' + '"')
		options = '--format=compact'

		cmd = 'java -jar ' + rhino_path + ' ' + csslint_rhino_js + ' ' + options + ' ' + path_argument.encode('utf-8')

		AsyncProcess(cmd, self)
		StatusProcess('Starting CSSLint for file ' + file_name, self)

	def update_status(self, msg, progress):
		sublime.status_message(msg + " " + progress)

	def append_data(self, proc, data, end=False):
		
		# truncate file paths but save them in an array.
		# add error number to each line - needed for finding full path.
		def munge_errors(data):
			data_all_lines      = data.split('\n')
			data_nonempty_lines = []
			self.errors         = []

			# remove empty lines
			for line in data_all_lines:
				if len(line) > 0:
					data_nonempty_lines.append(line)

			# truncate path for display, save full path in array.
			count = 1  # 1-indexing here
			for line in data_nonempty_lines:
				full_path_string   = line[0:line.find(':')]
				path_to_remove     = full_path_string[:full_path_string.rfind('/') + 1]
				cleaned_error_item = str(count) + ":" + line.replace(path_to_remove, '')
				found_error        = False

				def add_new_error():
					print 'adding errors'
					new_error_stylesheet = {
						'full_path': full_path_string,
						'items': [cleaned_error_item] 
					}
					self.errors.append(new_error_stylesheet)

				for error in self.errors:
					if error['full_path'] == full_path_string:
						found_error = True
						error['items'].append(cleaned_error_item)
						break
				
				if found_error == False:
					add_new_error()

				count += 1
		
		self.buffered_data = self.buffered_data + data.decode("utf-8")
		data               = self.buffered_data

		if self.file_paths:
			for path in self.file_paths:
				data = data.replace(path, path[path.rfind(FOLDER_MARKER):])
		else:
			data = self.buffered_data.replace(self.file_path, self.file_name).replace('\r\n', '\n').replace('\r', '\n')

		if end == False:
			rsep_pos = data.rfind('\n')
			if rsep_pos == -1:
				# not found full line.
				return
			self.buffered_data = data[rsep_pos+1:]
			data = data[:rsep_pos+1]

		munge_errors(data)
		print '----------------'
		print self.errors
		show_tests_panel(self)
		# selection_was_at_end = (len(self.output_view.sel()) == 1 and self.output_view.sel()[0] == sublime.Region(self.output_view.size()))
		self.output_view.set_read_only(False)
		edit = self.output_view.begin_edit()
		#self.output_view.insert(edit, self.output_view.size(), data)
		for error_section in self.errors:
			self.output_view.insert(edit, self.output_view.size(), '\n'.join(error_section['items']))
		self.output_view.end_edit(edit)
		self.output_view.set_read_only(True)

	def proc_terminated(self, proc):
		if proc.returncode == 0:
			# msg = self.file_name + ' lint free!'
			msg = ''
		else:
			msg = ''
		
		self.append_data(proc, msg, True)

		CsslintEventListener.disabled = False

class CsslintSelectionCommand(sublime_plugin.WindowCommand):
	def run(self, paths = []):
		self.window.run_command('csslint', {"paths": paths})

class CsslintEventListener(sublime_plugin.EventListener):
	disabled = False
	
	def __init__(self):
		self.previous_region = None
		self.file_view = None

	def on_selection_modified(self, view):
		if CsslintEventListener.disabled:
			return
		if view.name() != RESULT_VIEW_NAME:
			return
		region = view.line(view.sel()[0])

		# make sure call once.
		if self.previous_region == region:
			return
		self.previous_region = region

		# extract line from csslint result.
		text = view.substr(region)
		print text

		if len(text) < 2:
			return

		line = re.search('(?<=line\s)[0-9]+', text).group(0)

		# hightlight view line.
		view.add_regions(RESULT_VIEW_NAME, [region], "comment")

		# find the file view. FIXME: file_path is not in settings.
		file_path = view.settings().get('file_path')
		windows   = sublime.windows()
		file_view = None

		for window in windows:
			for v in window.views():
				if str(v.file_name()) in str(file_path):
					file_view = v
					break
		if file_view == None:
			print 'file_view is none'
			#sublime.active_window().open_file()
			return

		self.file_view = file_view
		window.focus_view(file_view)
		file_view.run_command("goto_line", {"line": line})
		file_region = file_view.line(file_view.sel()[0])

		# highlight file_view line
		file_view.add_regions(RESULT_VIEW_NAME, [file_region], "string")


def init_tests_panel(self):
	if not hasattr(self, 'output_view'):
		self.output_view = self.window.get_output_panel(RESULT_VIEW_NAME)
		self.output_view.set_name(RESULT_VIEW_NAME)
	clear_test_view(self)
	self.output_view.settings().set("file_path", self.file_path)

def show_tests_panel(self):
	if self.tests_panel_showed:
		return
	self.window.run_command("show_panel", {"panel": "output." + RESULT_VIEW_NAME})
	self.tests_panel_showed = True

def clear_test_view(self):
	self.output_view.set_read_only(False)
	edit = self.output_view.begin_edit()
	self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
	self.output_view.end_edit(edit)
	self.output_view.set_read_only(True)

def update_status(self, msg, progress):
	sublime.status_message(msg + " " + progress)
