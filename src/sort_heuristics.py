import datetime as dt


class ExamTime:
    def __init__(self, double_iso_string):
        start_time, end_time = double_iso_string.split("|")
        self.start_time = dt.datetime.fromisoformat(start_time)
        self.end_time = dt.datetime.fromisoformat(end_time)

    @property
    def avg_time(self):
        delta = self.end_time - self.start_time
        return self.start_time + (delta / 2)


class ExamSpread:
    """Utility class that computes heuristics based on spread of exam times."""

    YEAR = dt.datetime.now().year

    def __init__(self, json):
        self.json = json

    @staticmethod
    def _compute_date_spread(sorted_date_times):
        total_date_spread = dt.timedelta(0)
        for i in range(len(sorted_date_times) - 1):
            delta_consecutive = sorted_date_times[i + 1] - sorted_date_times[i]
            total_date_spread = total_date_spread + delta_consecutive
        return total_date_spread

    def __get_course_exam_times(self, timetable):
        course_exam_times = []
        COURSE_CLASSES = ["CDCs", "DEls", "HUELs", "OPELs"]
        for course in timetable:
            course_code, _ = course

            for course_class in COURSE_CLASSES:
                if course_code in (courses_dict := self.json[course_class]):
                    # currently does not try to parse time from
                    # "exams" as it too slow
                    exams_dict = courses_dict[course_code]["exams_iso"][0]
                    midsem_time_str = exams_dict.get("midsem", "")
                    compre_time_str = exams_dict.get("compre", "")
                    break

            else:
                raise Exception("Course code not found in any catagory")

            course_exam_times.append(
                (
                    course_code,
                    ExamTime(midsem_time_str) if midsem_time_str else None,
                    ExamTime(compre_time_str) if compre_time_str else None,
                )
            )
        return course_exam_times

    def __compute_exam_day_clash(self, exam_times):
        dates = set()
        exams_on_same_day = False
        for exam_time in exam_times:
            if (date_str := exam_time.date().isoformat()) in dates:
                exams_on_same_day = True
                break
            else:
                dates.add(date_str)
        return exams_on_same_day

    def compute(self, timetable_courses) -> tuple[float, bool]:
        """computes the exam_spread (total consecutive difference in the time of exams)
        along with if there are two exams on the same day.

        Args:
            timetable_courses (tuple): the courses contained in the timetable as a
              tuple of course code and list of sections chosen

        Returns:
            tuple of the of the type (float, bool) which contains the total exam
            spread seconds and also whether there are two exams on the same day
        """
        midsem_exam_times = []
        compre_exam_times = []
        for _, mid, compre in self.__get_course_exam_times(timetable_courses):
            if mid is not None:
                midsem_exam_times.append(mid.avg_time)
            if compre is not None:
                compre_exam_times.append(compre.avg_time)

        midsem_date_spread = self._compute_date_spread(sorted(midsem_exam_times))
        compre_date_spread = self._compute_date_spread(sorted(compre_exam_times))

        midsem_day_clash = self.__compute_exam_day_clash(midsem_exam_times)
        compre_day_clash = self.__compute_exam_day_clash(compre_exam_times)

        exams_on_same_day = midsem_day_clash or compre_day_clash

        return (
            (midsem_date_spread + compre_date_spread).total_seconds(),
            exams_on_same_day,
        )
