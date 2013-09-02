import os
import re
import sublime
import sublime_plugin
import subprocess

RESULT_VIEW_NAME = 'csslint_result_view'
RESULT_REGION_NAME = 'csslint_highlighted_region'
SETTINGS_FILE    = "CSSLint.sublime-settings"
PLUGIN_PATH = os.path.abspath(os.path.dirname(__file__))

print(os.path.join(PLUGIN_PATH, 'scripts/rhino/js.jar'))

if sublime.arch() == 'windows':
    FOLDER_MARKER = '\\'
else:
    FOLDER_MARKER = '/'


class CsslintCommand(sublime_plugin.TextCommand):

    def run(self, edit, paths=False):
        settings         = sublime.load_settings(SETTINGS_FILE)
        self.edit        = edit
        self.file_path   = None
        file_paths       = None
        self.file_paths  = None
        cssFiles         = []
        self.use_console = True

        def add_css_to_list(path):
            if path.endswith('.css'):
                cssFiles.append('"' + path + '"')

        # Make new document for lint results - we're linting multiple files.
        if paths is not False:
            self.use_console = False

            # Walk through any directories and make a list of css files
            for path in paths:
                if os.path.isdir(path) is True:
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

                # set up new file for lint results
                self.current_document = sublime.active_window().new_file()
                self.current_document.insert(self.edit,
                                             self.current_document.size(),
                                             'CSSLint Results\n\n')

        # Invoke console - we're linting a single file.
        else:
            if self.view.window().active_view().file_name() is None:
                sublime.error_message("CSSLint: Please save your file before linting.")
                return

            if self.view.window().active_view().file_name().endswith('css') is not True:
                sublime.error_message("CSSLint: This is not a css file.")
                return

            self.tests_panel_showed = False
            self.file_path = '"' + self.view.window().active_view().file_name() + '"'
            # init_tests_panel(self)
            show_tests_panel(self)

        # Begin linting.
        file_name          = os.path.basename(self.file_path) if self.file_path else ', '.join(self.file_paths)
        self.buffered_data = ''
        self.file_name     = file_name
        path_argument      = file_paths if file_paths else self.file_path
        self.is_running    = True
        rhino_path         = settings.get('rhino_path') if settings.has('rhino_path') and settings.get('rhino_path') != False else '"{0}"'.format(os.path.join(PLUGIN_PATH, 'scripts/rhino/js.jar'))
        csslint_rhino_js   = settings.get('csslint_rhino_js') if settings.has('csslint_rhino_js') and settings.get('csslint_rhino_js') != False else '"{0}"'.format(os.path.join(PLUGIN_PATH, 'scripts/csslint/csslint-rhino.js'))
        errors             = ' --errors=' + ','.join(settings.get('errors')) if isinstance(settings.get('errors'), list) and len(settings.get('errors')) > 0 else ''
        warnings           = ' --warnings=' + ','.join(settings.get('warnings')) if isinstance(settings.get('warnings'), list) and len(settings.get('warnings')) > 0 else ''
        ignores            = ' --ignore=' + ','.join(settings.get('ignore')) if isinstance(settings.get('ignore'), list) and len(settings.get('ignore')) > 0 else ''
        options            = '--format=compact' + errors + warnings + ignores
        cmd                = 'java -jar ' + rhino_path + ' ' + csslint_rhino_js + ' ' + options + ' ' + path_argument

        self.run_linter(cmd)

    def update_status(self, msg, progress):
        sublime.status_message(msg + " " + progress)

    def process_data(self, data, end=False):

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
            for line in data_nonempty_lines:
                full_path_string   = line[0:line.find('css:') + 3]
                path_to_remove     = full_path_string + ': '
                cleaned_error_item = line.replace(path_to_remove, '')
                found_error        = False

                def add_new_error():
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

                if found_error is False:
                    add_new_error()

        # Concatenate buffered data but prevent duplicates.
        self.buffered_data = self.buffered_data + data.decode("utf-8")
        data = self.buffered_data.replace('\r\n', '\n').replace('\r', '\n')

        if end is False:
            rsep_pos = data.rfind('\n')
            if rsep_pos == -1:
                # not found full line.
                return
            self.buffered_data = data[rsep_pos+1:]
            data = data[:rsep_pos+1]

        munge_errors(data)

        # Push to display.
        if self.use_console is True:
            self.output_to_console()
        else:
            self.output_to_document()

    def output_to_console(self):
        self.output_view.set_read_only(False)

        for error_section in self.errors:
            self.output_view.insert(self.edit, self.output_view.size(), '\n'.join(error_section['items']))

        self.output_view.set_read_only(True)
        CsslintEventListener.disabled = False

    def output_to_document(self):
        for error_section in self.errors:
            error_output = error_section['full_path'] + '\n\t' + '\n\t'.join(error_section['items']) + '\n\n'
            self.current_document.insert(self.edit, self.current_document.size(), error_output)

    def run_linter(self, cmd):
        self.proc = subprocess.Popen(cmd,
                                     env={"PATH": os.environ['PATH']},
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
            
        result = self.proc.communicate()[0]

        if result is not None:
            sublime.set_timeout(self.process_data(result), 0)


class CsslintSelectionCommand(sublime_plugin.WindowCommand):
    def run(self, paths=[]):
        self.view.window().run_command('csslint', {"paths": paths})


class CsslintEventListener(sublime_plugin.EventListener):
    disabled = False

    def __init__(self):
        self.previous_region = None
        self.file_view = None

    # for some reason on_selection_modified_async does not fire any events,
    # but this one does.
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

        if len(text) < 1:
            return

        line = re.search('(?<=line\s)[0-9]+', text).group(0)

        # hightlight view line.
        view.add_regions(RESULT_VIEW_NAME, [region], "comment")

        # highlight the selected line in the active view.
        file_view = sublime.active_window().active_view() if self.file_view is None else self.file_view
        file_view.run_command("goto_line", {"line": line})
        file_region = file_view.line(file_view.sel()[0])

        # highlight file_view line
        region_settings = sublime.DRAW_NO_FILL if hasattr(sublime, 'DRAW_NOFILL') else sublime.DRAW_OUTLINED
        file_view.add_regions(RESULT_REGION_NAME, [file_region], "string", "", region_settings)

        if hasattr(self, 'file_view') is True:
            self.file_view = file_view

    def on_deactivated(self, view):
        if view.name() == RESULT_VIEW_NAME:
            if hasattr(self, 'file_view'):
                self.file_view.erase_regions(RESULT_REGION_NAME)

def show_tests_panel(self):
    """Initializes (if not already initialized) and shows the results output panel."""
    if hasattr(self, 'tests_panel_shown') and self.tests_panel_shown is True:
        return

    if not hasattr(self, 'output_view'):
        try:  # ST3
            self.output_view = self.view.window().create_output_panel(RESULT_VIEW_NAME)
        except AttributeError: # ST2
            self.output_view = self.view.window().get_output_panel(RESULT_VIEW_NAME)

        self.output_view.set_name(RESULT_VIEW_NAME)

        # self.output_view.settings().set("file_path", self.file_path)

    clear_test_view(self)
    
    self.view.window().run_command("show_panel", {"panel": "output." + RESULT_VIEW_NAME})
    self.tests_panel_shown = True


def clear_test_view(self):
    self.output_view.set_read_only(False)
    self.output_view.erase(self.edit, sublime.Region(0, self.output_view.size()))
    self.output_view.set_read_only(True)
