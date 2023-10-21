from InquirerPy import inquirer
from functools import partial
from typing import List


class AskUserInput:
    WEEK_DAYS = ["Su", "M", "T", "W", "Th", "F", "S"]
    _fuzzy_selector = staticmethod(
        partial(
            inquirer.fuzzy,
            multiselect=True,
            height="70%",
        )
    )

    @classmethod
    def course_info(cls, course_choices: List[str]):
        """
        get user's selection of courses

        Args:

        course_choices(List[str]):
            array of courses which the user can choose from

        Returns:
            tuple of lists in the order CDCs, DELs, OPELs, HUELs
        """
        CDCs = cls._fuzzy_selector(
            "Select CDCs",
            choices=course_choices,
        ).execute()

        for course in CDCs:
            course_choices.remove(course)

        DEls = cls._fuzzy_selector(
            message="Select DEls",
            choices=course_choices,
            default="NONE",
        ).execute()

        for course in DEls:
            course_choices.remove(course)

        OPEls = cls._fuzzy_selector(
            message="Select OPELs",
            choices=course_choices,
            default="NONE",
        ).execute()

        for course in OPEls:
            course_choices.remove(course)

        HUEls = cls._fuzzy_selector(
            message="Select HUELs",
            choices=course_choices,
            default="NONE",
        ).execute()

        return (
            CDCs,
            DEls,
            HUEls,
            OPEls,
        )

    @staticmethod
    def _is_valid_permutation(result_list: List, orig_list: List):
        print(f"{result_list = }")
        if len(result_list) != len(orig_list):
            return False
        for item in orig_list:
            if item not in result_list:
                return False
        return True

    @staticmethod
    def _get_items_list(list_str: str):
        return [day.strip() for day in list_str.split(",")]

    @classmethod
    def work_load_spread(cls):
        """
        get user's preferences of workload spread over the week,
        in terms of free days and  liteness order of the weekdays.
        """
        free_days = cls._fuzzy_selector(
            message="Select freedays",
            choices=cls.WEEK_DAYS,
        ).execute()

        lite_order = inquirer.text(
            message="Arrange the days of the week in the order of liteness\n",
            filter=cls._get_items_list,
            validate=lambda input_str: cls._is_valid_permutation(
                cls._get_items_list(input_str), cls.WEEK_DAYS
            ),
            invalid_message="lite order must be a permutation of weekdays",
        ).execute()

        return (lite_order, free_days)
