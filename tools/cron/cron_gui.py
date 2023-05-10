#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

import tkinter as tk


class RequestPuller:
    def __init__(self, name, pull_time_offset, toggle_cb, state=True):
        self.name = name
        self.toggle_cb = toggle_cb
        # BooleanVar to hold the on/off state of each puller instance
        self.state = tk.BooleanVar()
        self.state.set(state)
        self.pull_time_offset = tk.IntVar(value=pull_time_offset)
        self.checkbutton = None
        self.entry = None


class CronGUI:
    def __init__(self, cancel_job_cb):
        self.root = tk.Tk()
        self.root.title('Cron GUI')
        self.cancel_job_cb = cancel_job_cb

        # Configure columns and rows to stretch with a scalar of 1.
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Create a list of job dictionaries, with each dictionary containing the job name and its information
        self.job_list = []

        job_list_pane = tk.PanedWindow(self.root)
        job_list_pane.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Create a Listbox to display the job names
        self.listbox = tk.Listbox(job_list_pane)
        self.update_job_list(self.job_list)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        button_pane = tk.PanedWindow(job_list_pane)
        button_pane.pack()

        # Create a function to display the information of the selected job
        def show_job_info(event=None):
            selection = self.listbox.curselection()
            if selection:
                index = selection[0]
                job_info = self.job_list[index]['info']
                info_text.delete('1.0', tk.END)
                info_text.insert('1.0', job_info)

        # Bind the function to the Listbox's <<ListboxSelect>> event
        self.listbox.bind('<<ListboxSelect>>', show_job_info)

        # Create a Button to cancel the selected job
        cancel_button = tk.Button(button_pane, text='Cancel job', command=self.cancel_job)
        cancel_button.pack()

        # Bind the Delete key to the cancel_job() function
        self.listbox.bind('<Delete>', lambda event: self.cancel_job())

        # Create a Text widget to display the job information
        info_text = tk.Text(self.root, height=10, width=50)
        info_text.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        # Create a list of puller instances
        self.pullers = []

        # Create a set of Checkbuttons and entry widgets to control the on/off state
        # and parameter value of each puller instance
        self.puller_checkbuttons_pane = tk.PanedWindow(self.root)
        self.puller_checkbuttons_pane.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        on_of_label = tk.Label(self.puller_checkbuttons_pane, text='Pullers:')
        on_of_label.grid(row=0, column=0, sticky='w')
        pull_delay_label = tk.Label(self.puller_checkbuttons_pane, text='Pull time offset:')
        pull_delay_label.grid(row=0, column=1, sticky='e')

    def mainloop(self):
        """Blocking loop, required to call in main thread."""
        self.root.mainloop()

    def update_job_list(self, job_list):
        """Updates the list of the cron jobs."""
        for _ in self.job_list:
            self.listbox.delete(0)

        self.job_list.clear()
        self.job_list.extend(job_list)
        for job in self.job_list:
            self.listbox.insert(tk.END, job['name'])

    def cancel_job(self):
        """Removes the selected job from the list"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.listbox.delete(index)
            job = self.job_list.pop(index)
            self.cancel_job_cb(job['name'])

    def update_puller_list(self, puller_list):
        """Updates the list of puller check buttons"""
        for puller in self.pullers:
            puller.checkbutton.grid_remove()
        self.pullers.clear()
        self.pullers.extend(puller_list)

        for i, puller in enumerate(self.pullers):
            # Define a function to be called when the Checkbutton is toggled
            def toggle_puller(_puller=puller):
                _puller.toggle_cb(
                    _puller.name,
                    _puller.state.get(),
                    _puller.pull_time_offset.get())

            puller.cb = tk.Checkbutton(self.puller_checkbuttons_pane,
                                       text=puller.name,
                                       variable=puller.state,
                                       command=toggle_puller)
            puller.cb.grid(row=i + 1, column=0, sticky='w')
            puller.entry = tk.Entry(self.puller_checkbuttons_pane,
                                    textvariable=puller.pull_time_offset,
                                    width=5)
            puller.entry.grid(row=i + 1, column=1, padx=5, pady=5, sticky='e')
