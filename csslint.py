import os
import re
import sublime
import sublime_plugin
import platform
from statusprocess import *
from asyncprocess import *

RESULT_VIEW_NAME = 'csslint_result_view'
SETTINGS_FILE = "CSSLint.sublime-settings"

class CsslintCommand(sublime_plugin.WindowCommand):  
	def run(self, paths = False):  
		settings = sublime.load_settings('SETTINGS_FILE')

		if paths != False:

			cssFiles = []

			for path in paths:
				if os.path.isdir(path) == True:
					for path, subdirs, files in os.walk(path):
					    for name in files:
							thisFile = os.path.join(path, name)
							if thisFile.endswith('.css'):
								cssFiles.append('"' + thisFile + '"')
				
				elif path.endswith('.css'):
					cssFiles.append["'" + path + "'"]

			if len(cssFiles) < 1:
				print "No CSS files found."
				return

			else:
				file_path = ' '.join(cssFiles)
				print file_path
				
		else:
			if self.window.active_view().file_name() == None:
				print "csslint: Please save your file before running this command."
				return

			file_path = '"' + self.window.active_view().file_name() + '"'
		
		file_name = os.path.basename(file_path)

		self.buffered_data = ''
		self.file_path = file_path
		self.file_name = file_name
		self.is_running = True
		self.tests_panel_showed = False

		self.init_tests_panel()
		
		# create the csslint command for node
		# cmd = 'csslint' + ' --format=compact ' + " '" + file_path.encode('utf-8') + "'"

		rhino_path = settings.get('rhino_path', '"' + sublime.packages_path() + '/CSSLint/scripts/rhino/js.jar' + '"')
		csslint_rhino_js = settings.get('csslint_rhino_js', '"' + sublime.packages_path() + '/CSSLint/scripts/csslint/csslint-rhino.js' + '"')
		options = '--format=compact'

		cmd = 'java -jar ' + rhino_path + ' ' + csslint_rhino_js + ' ' + options + ' ' + file_path.encode('utf-8')
 		print cmd
		AsyncProcess(cmd, self)
		StatusProcess('Starting CSSLint for file ' + file_name, self)

	def init_tests_panel(self):
		if not hasattr(self, 'output_view'):
			self.output_view = self.window.get_output_panel(RESULT_VIEW_NAME)
			self.output_view.set_name(RESULT_VIEW_NAME)
		self.clear_test_view()
		self.output_view.settings().set("file_path", self.file_path)

	def show_tests_panel(self):
		if self.tests_panel_showed:
			return
		self.window.run_command("show_panel", {"panel": "output."+RESULT_VIEW_NAME})
		self.tests_panel_showed = True

	def clear_test_view(self):
		self.output_view.set_read_only(False)
		edit = self.output_view.begin_edit()
		self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
		self.output_view.end_edit(edit)
		self.output_view.set_read_only(True)

	def append_data(self, proc, data, end=False):
		self.buffered_data = self.buffered_data + data.decode("utf-8")
		data = self.buffered_data.replace(self.file_path, self.file_name).replace('\r\n', '\n').replace('\r', '\n')
		arrData = data.split('\n\n')

		if end == False:
			rsep_pos = data.rfind('\n')
			if rsep_pos == -1:
				# not found full line.
				return
			self.buffered_data = data[rsep_pos+1:]
			data = data[:rsep_pos+1]

		self.show_tests_panel()
		selection_was_at_end = (len(self.output_view.sel()) == 1 and self.output_view.sel()[0] == sublime.Region(self.output_view.size()))
		self.output_view.set_read_only(False)
		edit = self.output_view.begin_edit()
		self.output_view.insert(edit, self.output_view.size(), data)
		
		self.output_view.end_edit(edit)
		self.output_view.set_read_only(True)

	def update_status(self, msg, progress):
		sublime.status_message(msg + " " + progress)

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
		self.previous_resion = None
		self.file_view = None
	
	def on_selection_modified(self, view):
		if CsslintEventListener.disabled:
			return
		if view.name() != RESULT_VIEW_NAME:
			return
		region = view.line(view.sel()[0])

		# make sure call once.
		if self.previous_resion == region:
			return
		self.previous_resion = region

		# extract line from csslint result.
		text = view.substr(region)

		if len(text) < 2:
			return

		line = re.search('(?<=line\s)[0-9]+', text).group(0)

		# hightligh view line.
		view.add_regions(RESULT_VIEW_NAME, [region], "comment")

		# find the file view.
		file_path = view.settings().get('file_path')
		window = sublime.active_window()
		file_view = None
		for v in window.views():
			if v.file_name() == file_path:
				file_view = v
				break
		if file_view == None:
			return

		self.file_view = file_view
		window.focus_view(file_view)
		file_view.run_command("goto_line", {"line": line})
		file_region = file_view.line(file_view.sel()[0])

		# highlight file_view line
		file_view.add_regions(RESULT_VIEW_NAME, [file_region], "string")