from InquirerPy import inquirer
from InquirerPy.base.control import Choice as InquirerPyChoice
from typing import Optional
from operator import getitem
from functools import wraps, partial, reduce
from collections import defaultdict

Choice = InquirerPyChoice


class AskUserInput:
    WEEK_DAYS = ["Su", "M", "T", "W", "Th", "F", "S"]

    @staticmethod
    @wraps(inquirer.fuzzy)
    def fuzzy_select(
        prompt_message,
        choices,
        *args,
        multiselect=True,
        height="70%",
        **kwargs,
    ):
        """
        select one (or more,if multiselect is enabled) out of the given set of choices
        by fuzzy matching the option name with the user input

        Args:
            prompt_message(str): the prompt string to use to prompt user
            choices(list): the list of possible choices values,
                of which the return list will be a subset of. (flattened if multiselect is disabled)
            multiselect(bool): whether to allow the user to select multiple choices out of the given ones.

        Returns:
            selection or list of selections if multiselect is disabled or enabled respectively
        """
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
    def course_info(cls, course_choices: list[str]):
        """
        get user's selection of courses for seperated into each class
        of courses i.e CDC, DEL, OPEL, HUEL

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
            OPEls,
            HUEls,
        )

    @staticmethod
    def is_valid_elective_number(num_str: str, n_elective_courses):
        try:
            num = int(num_str)
            return 0 < num <= n_elective_courses
        except ValueError:
            return False

    @classmethod
    def ask_number_of_each_elective(
        cls, total_electives_number
    ) -> tuple[int, int, int]:
        """fetches the number of each elective type that the user
        wants in their timetable

        Args:
            total_electives_number(tuple): tuple containing total number of courses within
              each elective class. in the order DEl, OPEls, HUEls


        Returns:
            tuple containing the user's choice of size of each electives class.
            in the order DEls, OPEls, HUels.
        """
        COURSE_CLASS_ORDER = ("DEls", "OPEls", "HUEls")
        result_list = [0, 0, 0]
        for i, (total_courses, course_class) in enumerate(
            zip(total_electives_number, COURSE_CLASS_ORDER)
        ):
            if total_courses != 0:
                result_list[i] = cls.ask_text(
                    f"How many {course_class} should be included in the timetable?",
                    validator=partial(
                        cls.is_valid_elective_number,
                        n_elective_courses=total_courses,
                    ),
                )

        return tuple(result_list)

    @staticmethod
    def _is_valid_permutation(result_list: list, orig_list: list):
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
    def work_load_spread(cls, **kwargs):
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
            **kwargs,
        )

        return (lite_order, free_days)

    @staticmethod
    def _non_empty_sections_validator(
        excluded_section_indices: Optional[list[tuple]],
        sect_seperated_json: dict,
    ):
        """
        validation predicate that checks (returns true),
        if all sections of section type of any course
        have not been excluded i.e that there is atleast one
        section left in each of the section types for each of the courses.

        Args:
            sect_seperated_json: filtered json containing course
              sections seperated by section type
            excluded_section_indices: tuple indices of the sect_seperated_json
        """
        # if no sections are selected return immediately
        # (the default choice NONE matches nothing)
        if not excluded_section_indices:
            return True

        # dict of the form
        # {(course_class, course_name, section_type): [<excluded section numbers>]}
        excluded_sections_info = defaultdict(set)
        for parent_index_tuple, section in excluded_section_indices:
            excluded_sections_info[parent_index_tuple].add(section)

        for parent_index_tuple, excluded_sections in excluded_sections_info.items():
            all_course_sections_of_type = set(
                # use keys in order of appearence in parent index tuple
                # to index deeper into the dict
                # reduce(getitem, ('a','b','c'), {'a':{'b':{'c': "hello"}}}) -> "hello"
                reduce(
                    getitem,
                    parent_index_tuple,
                    sect_seperated_json,
                )
            )

            # compute difference of all courses minus the excluded courses
            # to get not excluded courses
            sections_not_excluded = all_course_sections_of_type.difference(
                excluded_sections
            )
            return len(sections_not_excluded) != 0

    @classmethod
    def get_excluded_sections(
        cls,
        section_choices,
        sect_seperated_json,
        **kwargs,
    ):
        """asks users for sections which should not be included in the timetable

        Args:
            section_choices  (List[Union[Choice, str]]): the choices which are to be passed to fuzzy selector
            sect_seperated_json (Dict): filtered json with each section seperated by section type
        """
        return cls.fuzzy_select(
            "Choose Excluded Sections: ",
            section_choices,
            default="NONE",
            validate=partial(
                cls._non_empty_sections_validator,
                sect_seperated_json=sect_seperated_json,
            ),
            invalid_message="Cannot exclude all courses of a type",
            **kwargs,
        )
