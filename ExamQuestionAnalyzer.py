import os
import re
import sys
import tkinter.filedialog as tkf

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('TkAgg')
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ExamQuestionAnalyzer(tk.Frame):
    """
    This is the header (title) of the first column in the errorcodes file
    """
    ERROR_CODE_HEADER = 'Error Code'

    def __init__(self, manual_grading_filename=None, errorcodes_filename=None, default_grade=100,
                 range_constraint=None):

        super().__init__(master=tk.Tk())
        self.range_constraint = range_constraint
        self.default_grade = default_grade
        self._fill_frame()
        self.figure: plt.Figure = plt.figure()
        self.ax: plt.Axes = self.figure.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, self.master)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM)
        self.manual_grading_filename = manual_grading_filename
        self.errorcodes_filename = errorcodes_filename
        if self.manual_grading_filename:
            self.ax.set_title(os.path.basename(self.manual_grading_filename))
        if self.manual_grading_filename: self._load_manual_grading_file()
        if self.errorcodes_filename: self._load_errorcodes_file()
        self.master.update()

    def _fill_frame(self):
        self.master.protocol("WM_DELETE_WINDOW", self._close_window)
        self.load_manual_grading_button = tk.Button(self.master, text="Load manual grading",
                                                    command=self.get_manual_grading)
        self.load_errorcodes_button = tk.Button(self.master, text="Load errorcodes", command=self.get_errorcodes)
        self.calc_grades_button = tk.Button(self.master, text="Calculate grades", command=self.calculate_grades)
        self.plot_button = tk.Button(self.master, text="Plot grades", command=self.plot)
        self.plot_button.pack(side=tk.BOTTOM)
        self.calc_grades_button.pack(side=tk.BOTTOM)
        self.load_manual_grading_button.pack(side=tk.BOTTOM)
        self.load_errorcodes_button.pack(side=tk.BOTTOM)

    def get_manual_grading(self):
        res = tk.messagebox.askyesno('Load file', 'would you like to load a new file new file?')
        if res:
            self.manual_grading_filename = tkf.askopenfilename(title="Please choose the grading file:",
                                                               default=os.curdir)
        self._load_manual_grading_file()

    def _load_manual_grading_file(self):
        try:
            with open(self.manual_grading_filename, 'r') as file:
                text = file.read()
        except UnicodeDecodeError:
            with open(self.manual_grading_filename, 'r', encoding="utf8") as file:
                text = file.read()
        split_text = re.split("\n\n", text)
        data = [
            {"cse_name": t[0][:-1],
             "comment_list": [s[:s.find("{") if "{" in s else len(s)].strip() for s in t[1:] if s and s[0] != "{"],
             "grade": self.default_grade}
            for t in [re.split("\n\t", txt) for txt in split_text]]
        self.manual_grading_df = pd.DataFrame(data)

    def get_errorcodes(self):
        res = tk.messagebox.askyesno('Load file', 'would you like to load a new file new file?')
        if res:
            self.errorcodes_filename = tkf.askopenfilename(title="Please choose the errorcodes file:",
                                                           default=os.curdir)
        self._load_errorcodes_file()

    def _load_errorcodes_file(self):
        if ".csv" in self.errorcodes_filename:
            self.errorcodes_df = pd.read_csv(self.errorcodes_filename)
        elif ".xls" in self.errorcodes_filename or ".xlsx" in self.errorcodes_filename:
            self.errorcodes_df = pd.read_excel(self.errorcodes_filename)
        else:  # if the above are not correct, assume \t is the separator
            self.errorcodes_df = pd.read_csv(self.errorcodes_filename, sep="\t")
        self.errorcodes_df = self.errorcodes_df.set_index(self.ERROR_CODE_HEADER).T.to_dict('list')

    def calculate_grades(self):
        # make sure the files are the most updated before calculating
        if not self.manual_grading_filename:
            raise ValueError("Manual grading file not loaded! Please load before calculating grades")
        if not self.errorcodes_filename:
            raise ValueError("Manual grading file not loaded! Please load before calculating grades")
        self._load_manual_grading_file()
        self._load_errorcodes_file()
        self.grades = np.full((len(self.manual_grading_df.index)), self.default_grade)
        for i, row in self.manual_grading_df.iterrows():
            for comment in row[1]:
                if comment not in self.errorcodes_df.keys():
                    if comment[-1] == ")":  # there is a penalty-determining parenthesis in the comment
                        point_reduction = comment[comment.find("(") + 1:-1]
                        if "/" in point_reduction:  # assume it is max/x
                            self.grades[i] += self.errorcodes_df[comment[:comment.find("(")]][0] / float(
                                point_reduction[point_reduction.find("/") + 1:])
                            continue
                        else:  # it is just a number
                            self.grades[i] += float(point_reduction)
                            continue
                    # display the unknown errorcode, so that you can fix it
                    print(f"The error code '{comment}' is not is the errorcodes file", file=sys.stderr)
                    continue
                self.grades[i] += self.errorcodes_df[comment][0] if (not pd.isna(self.errorcodes_df[comment][0])) else 0
        # display student names that exceed the possible range of grades
        if (self.grades < 0).sum() > 0:
            print(f"The Following cse names have lower than 0 grades:", file=sys.stderr)
            print(self.manual_grading_df.loc[self.grades < 0, 'cse_name'], file=sys.stderr)
        if (self.grades > (self.range_constraint if self.range_constraint else 100)).sum() > 0:
            print(
                f"\nThe Following cse names have higher than {self.range_constraint if self.range_constraint else 100} grades:",
                file=sys.stderr)
            print(self.manual_grading_df.loc[
                      self.grades > (self.range_constraint if self.range_constraint else 100), 'cse_name'],
                  file=sys.stderr)

    def plot(self):
        """
        Plot the histogram
        """
        self.ax.clear()
        self.ax.set_title(os.path.basename(self.manual_grading_filename))
        self.ax.set_xlabel("grade")
        self.ax.set_ylabel("count")
        range = np.arange(min(0, self.grades.min()), 101, 5) if not self.range_constraint else np.arange(0,
                                                                                                         self.range_constraint + 1,
                                                                                                         self.range_constraint / 10)
        self.ax.hist(self.grades, bins=range)
        self.ax.set_xticks(range)
        self.ax.text(0.05, 0.8,
                     f"Mean: {self.grades.mean():.2f}\nMedian: {np.median(self.grades):.2f}\nSD: {np.std(self.grades):.2f}",
                     transform=self.ax.transAxes)
        self.canvas.draw()
        self.master.update()

    def _close_window(self):
        plt.close(self.figure)
        self.master.destroy()
