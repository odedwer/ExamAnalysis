# ExamAnalysis
Simple histogram with mean tendencies GUI for CS exam grading.

Each instance of the ExamQuestionAnalyzer class will open a new tkinter frame.
Every time you press "calculate grades", the files are re-loaded and parsed, so that you may change penalties and codes with the GUI open.
Press plot to see the histogram for the current grades.

In case there are penalties which appear in the manual grading but not in the error codes, a message will be printed to stderr.
In case students have illogical grades (below 0/above the upper threshold for grades, default 100) their CSE usernames will be printed to stderr.

