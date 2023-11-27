# Quiz #1: Identify class hierarchy as a forest

Your submission must satisfy the following requirements:

* R1. Shall initialize your assignment repository from
* R2. Write your `app_analyzer.py` in the repository.
* R3. Test your `app_analyzer.py` by using `pytest`.
* R4. You need to let your TA know your repository URL and your student ID together via Slack.
* R5. Check out `test_analyzer1.py` to figure out the output format.
* R6. Assume that there are nested classes/methods and anonymous classes.
* R7. Assume that there are nested directories in the input path.
* R8. The function `collect_class_forest(...)` takes a path of a directory containing multiple python source code files, and produces a map of classes. The keys of the map are root classes that have no parent classes and have at least one child class. Each child class can have a set of children classes if the class has generalization relationships with other classes. If the class has no more children classes, an empty dictionary (`{}`) should be added at the end.
* R9. Assume that there is no multiple inheritance between classes.


## Note:

* N1. `pytest` (based on `test_analyzer1.py`) is just for validating your program. The final grading will be made by other test cases.
* N2. Submissions via GitHub Classroom will only be accepted. Submissions via LMS or any other means are not accepted.
* N3. DO NOT change files in this repository except for `app_analyzer.py`. Adding new files are allowed.
* N4. Late submissions after 4:15pm are *NOT* allowed.

