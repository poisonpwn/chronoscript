from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from typing import List
from functools import wraps


class AskUserInput:
    WEEK_DAYS = ["Su", "M", "T", "W", "Th", "F", "S"]

    @staticmethod
    @wraps(inquirer.fuzzy)
    def fuzzy_select(
        prompt_message, choices, *args, multiselect=True, height="70%", **kwargs
    ):
        handle = inquirer.fuzzy(
            *args,
            message=prompt_message,
            choices=choices,
            multiselect=multiselect,
            height=height,
            **kwargs,
        )
        return handle.execute()

    @staticmethod
    @wraps(inquirer.text)
    def ask_text(prompt_message, *args, **kwargs):
        handle = inquirer.text(message=prompt_message, *args, **kwargs)
        return handle.execute()

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
        CDCs = cls.fuzzy_select(
            "Select CDCs",
            choices=course_choices,
        )

        for course in CDCs:
            course_choices.remove(course)

        DEls = cls.fuzzy_select(
            "Select DEls",
            course_choices,
            default="NONE",
        )

        for course in DEls:
            course_choices.remove(course)

        OPEls = cls.fuzzy_select(
            "Select OPELs",
            course_choices,
            default="NONE",
        )

        for course in OPEls:
            course_choices.remove(course)

        HUEls = cls.fuzzy_select(
            "Select HUELs",
            course_choices,
            default="NONE",
        )

        return (
            CDCs,
            DEls,
            HUEls,
            OPEls,
        )

    @staticmethod
    def _is_valid_permutation(result_list: List, orig_list: List):
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
        free_days = cls.fuzzy_select(
            "Select freedays",
            cls.WEEK_DAYS,
        )

        lite_order = cls.ask_text(
            "Arrange the days of the week in the order of liteness\n",
            filter=cls._get_items_list,
            validate=lambda input_str: cls._is_valid_permutation(
                cls._get_items_list(input_str), cls.WEEK_DAYS
            ),
            invalid_message="lite order must be a permutation of weekdays",
        )

        return (lite_order, free_days)

    @classmethod
    def get_excluded_sections(cls, section_infos):
        section_choices = []
        for section_info in section_infos:
            _, course_name, section = section_info
            section_choices.append(
                Choice(section_info, name=f"{course_name} - {section}")
            )
        return cls.fuzzy_select(
            "Choose Excluded Sections: ",
            section_choices,
            default="NONE",
        )
