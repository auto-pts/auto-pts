import logging
import queue
import tkinter as tk
from tkinter import messagebox, ttk

from autopts.ptsprojects.ptstypes import MMI_STYLE_STRING
from autopts.types import PTSProxy

log = logging.debug


class WIDDialog:
    def __init__(self, parent, callback):
        self._parent = parent
        self._callback = callback
        self._test_case_status = None
        self._dialog_window = None
        self._project_name = None
        self._test_case_name = None
        self._mmi_entry = None
        self._description_entry = None
        self._selected_style = tk.StringVar()
        self._selected_status = tk.StringVar()

    def open_dialog(self, project_name, test_case_name, mmi_response, lt_name):
        if self._dialog_window is not None:
            return

        self._project_name = project_name
        self._test_case_name = test_case_name

        self._dialog_window = tk.Toplevel(self._parent)
        self._dialog_window.title(f"{lt_name} MMI entry dialog")
        self._dialog_window.protocol("WM_DELETE_WINDOW", self.end_test_case)

        mmi_label = tk.Label(self._dialog_window, text='MMI ID:', width=40)
        mmi_label.pack(pady=10)

        self._mmi_entry = tk.Entry(self._dialog_window, width=40)
        self._mmi_entry.pack(pady=10)

        mmi_style_label = tk.Label(self._dialog_window, text='MMI style:', width=40)
        mmi_style_label.pack(pady=10)

        style_options = list(MMI_STYLE_STRING.values())
        self._selected_style.set(style_options[0])
        dropdown = tk.OptionMenu(self._dialog_window, self._selected_style, *style_options)
        dropdown.pack(pady=10)

        mmi_description_label = tk.Label(self._dialog_window, text='MMI description:', width=40)
        mmi_description_label.pack(pady=10)

        self._description_entry = tk.Text(self._dialog_window, height=5, width=40)
        self._description_entry.pack(pady=10)

        submit_button = tk.Button(self._dialog_window, text="Submit MMI", command=self.on_submit,
                                  fg='white', bg='#4287f5')
        submit_button.pack(pady=10)

        separator = ttk.Separator(self._dialog_window, orient='horizontal')
        separator.pack(fill='x')

        tc_status_label = tk.Label(self._dialog_window, text='Test case status:', width=40)
        tc_status_label.pack(pady=10)

        status_options = ['PASS', 'FAIL', 'INCONC']
        self._selected_status.set(status_options[0])
        status_dropdown = tk.OptionMenu(self._dialog_window, self._selected_status, *status_options)
        status_dropdown.pack(pady=10)

        end_test_case_button = tk.Button(self._dialog_window, text="End test case",
                                         command=self.end_test_case, fg='white', bg='#d14555')
        end_test_case_button.pack(pady=10)

        close_button = tk.Button(self._dialog_window, text="Close", command=self.close_dialog)
        close_button.pack(pady=10)

        if mmi_response:
            separator = ttk.Separator(self._dialog_window, orient='horizontal')
            separator.pack(fill='x')

            mmi_response_label = tk.Label(self._dialog_window, text='MMI response:', width=40)
            mmi_response_label.pack(pady=10)

            mmi_response_text = tk.Text(self._dialog_window, height=5, width=40)
            mmi_response_text.pack(pady=10)
            mmi_response_text.insert(tk.END, mmi_response)

    def close_dialog(self):
        if self._dialog_window is not None:
            self._dialog_window.destroy()
            self._dialog_window = None

    def is_closed(self):
        return self._dialog_window is None

    def end_test_case(self):
        self._test_case_status = self._selected_status.get()
        self._callback.set_result('run_test_case', self._test_case_status)
        self.close_dialog()

    def on_submit(self):
        if self._dialog_window is None:
            return

        try:
            wid = int(self._mmi_entry.get())
        except ValueError:
            messagebox.showerror("Invalid MMI ID", "MMI ID must be an integer.")
            return
        description = self._description_entry.get("1.0", "end-1c")
        selected_style = self._selected_style.get()

        style = None
        for key, val in MMI_STYLE_STRING.items():
            if val == selected_style:
                style = key
                break

        self._callback.on_implicit_send(self._project_name, wid, self._test_case_name, description, style)
        self.close_dialog()

    def get_test_case_status(self):
        return self._test_case_status


class PTSGUIProxy(PTSProxy):
    root_window = None
    task_queue = queue.Queue()

    def __init__(self, args, callback, pts_addr, name):
        self.info = "PTS GUI proxy"
        self.name = name
        self._pts_version = 'Unknown, GUI mode'
        self._bd_addr = pts_addr
        self._test_cases = self._parse_test_cases(args.test_cases)
        self._wid_dialog = None
        self._ask_for_wid_pending = False
        self._project_name = None
        self._test_case_name = None
        self._last_mmi_response = ''
        self.callback_thread = None
        self.callback = callback
        self._init_root()

    def __getattr__(self, item):
        return self._generic

    def _generic(self, *args, **kwargs):
        return True

    def _init_root(self):
        if not PTSGUIProxy.root_window:
            root = tk.Tk()
            PTSGUIProxy.root_window = root
            root.title("GUI root")
            root.attributes("-topmost", 1)
            root.withdraw()
            root.after(1000, PTSGUIProxy.check_queue)

    def _parse_test_cases(self, test_cases):
        parsed = {}
        for tc in test_cases:
            prefix = tc.split('/')[0]
            if prefix not in parsed:
                parsed[prefix] = []

            parsed[prefix].append(tc)

        return parsed

    def get_version(self):
        return self._pts_version

    def bd_addr(self):
        return self._bd_addr

    def restart_pts(self):
        self.callback.set_result('restart_pts', True)
        return "WAIT"

    def get_project_list(self):
        return self._test_cases.keys()

    def get_test_case_list(self, project):
        return self._test_cases[project]

    def get_test_case_description(self, project_name, test_case_name):
        return ''

    def list_workspace_tree(self, workspace_dir):
        return []

    def set_pixit(self, project_name, param_name, param_value):
        log(f'Set PIXIT: {project_name} {param_name} {param_value}')

    def update_pixit_param(self, project_name, param_name, param_value):
        log(f'Update PIXIT: {project_name} {param_name} {param_value}')

    def run_test_case(self, project_name, test_case_name):
        self._project_name = project_name
        self._test_case_name = test_case_name
        return 'WAIT'

    def set_wid_response(self, response):
        self._last_mmi_response = response

    def ask_for_wid(self):
        if not self._ask_for_wid_pending and (self._wid_dialog is None or self._wid_dialog.is_closed()):
            self._ask_for_wid_pending = True
            PTSGUIProxy.task_queue.put(self._ask_for_wid)

    def _ask_for_wid(self):
        self._ask_for_wid_pending = False
        status = None
        if self._wid_dialog is not None and self._wid_dialog.is_closed():
            status = self._wid_dialog.get_test_case_status()
            self._wid_dialog = None

        if status is None and self._wid_dialog is None:
            self._wid_dialog = WIDDialog(PTSGUIProxy.root_window, self.callback)
            self._wid_dialog.open_dialog(self._project_name, self._test_case_name,
                                         self._last_mmi_response, self.name)

    @staticmethod
    def check_queue():
        try:
            if PTSGUIProxy.root_window is None:
                return

            fn = PTSGUIProxy.task_queue.get_nowait()
        except queue.Empty:
            pass
        except AttributeError:
            return
        else:
            fn()
        finally:
            if PTSGUIProxy.root_window:
                PTSGUIProxy.root_window.after(100, PTSGUIProxy.check_queue)

    def stop_mainloop(self):
        if PTSGUIProxy.root_window:
            PTSGUIProxy.task_queue.put(PTSGUIProxy.root_window.quit)

    def mainloop(self):
        self._init_root()
        try:
            if PTSGUIProxy.root_window:
                PTSGUIProxy.root_window.mainloop()
        finally:
            PTSGUIProxy.root_window = None
