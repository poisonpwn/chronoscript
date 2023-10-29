import json
from itertools import product, combinations
from typing import Annotated, Optional
from prompt_user import AskUserInput, Choice
from sort_heuristics import ExamSpread

DAYS = ["M", "T", "W", "Th", "F", "S", "Su"]
EXAM_FIT_STRATEGIES = {
    "Close Together": 1,
    "Spaced Apart": -1,
}


def get_filtered_json(
    json: Annotated[dict, "main timetable json file"],
    CDCs: Annotated[list[str], "list of BITS codes for CDCs selected"],
    DEls: Annotated[list[str], "list of BITS codes for DEls selected"],
    HUELs: Annotated[list[str], "list of BITS codes for HUELs selected"],
    OPELs: Annotated[list[str], "list of BITS codes for OPELs selected"],
) -> dict:
    """
    Function to filter the main timetable json file to only include the selected courses

    Args:
        json (dict): main timetable json file
        CDCs (list[str]): list of BITS codes for CDCs selected
        DEls (list[str]): list of BITS codes for DEls selected
        HUELs (list[str]): list of BITS codes for HUELs selected
        OPELs (list[str]): list of BITS codes for OPELs selected

    Returns:
        dict: filtered json file, i.e, with only courses selected
    """
    json = json["courses"]

    filtered_json = {"CDCs": {}, "DEls": {}, "HUELs": {}, "OPELs": {}}
    for CDC in CDCs:
        filtered_json["CDCs"][CDC] = json[CDC]
    for DEL in DEls:
        filtered_json["DEls"][DEL] = json[DEL]
    for HUEL in HUELs:
        filtered_json["HUELs"][HUEL] = json[HUEL]
    for OPEL in OPELs:
        filtered_json["OPELs"][OPEL] = json[OPEL]
    return filtered_json


def separate_sections_into_types(
    filtered_json: Annotated[
        dict, "filtered json file, i.e, with only courses selected"
    ]
) -> dict:
    """
    Function to separate the sections into lectures, tutorials and practicals

    Args:
        filtered_json (dict): filtered json file, i.e, with only courses selected

    Returns:
        dict: dictionary of courses' sections separated into lectures, tutorials and practicals
    """
    sep = {}

    for type in filtered_json:
        sep[type] = {}
        for course in filtered_json[type]:
            lectures = []
            tutorials = []
            practicals = []
            # inner dictionary we'll be continuously referring to
            ref = filtered_json[type][course]
            for section in ref["sections"]:
                if section.startswith("L"):
                    lectures.append(section)
                elif section.startswith("T"):
                    tutorials.append(section)
                elif section.startswith("P"):
                    practicals.append(section)
            sep[type][course] = {
                "L": lectures,
                "T": tutorials,
                "P": practicals,
            }
            # if list is empty remove the key-value pair
            # we need to remove it as it causes problems when using woth itertools.product()
            if not lectures:
                del sep[type][course]["L"]
            if not tutorials:
                del sep[type][course]["T"]
            if not practicals:
                del sep[type][course]["P"]
    return sep


def generate_intra_combinations(
    sect_seperated_json: Annotated[
        dict, "filtered json with courses seperated into sections"
    ],
) -> dict:
    """
    Function that generates all possible combinations of sections within each course

    Args:
        filtered_json (dict): filtered json file, i.e, with only courses selected

    Returns:
        dict: dictionary of all possible combinations of sections within each course
    """

    combs = {}
    for type in sect_seperated_json:
        combs[type] = {}
        for course in sect_seperated_json[type]:
            sections = []
            # first check is the type of section (L, T or P) is present in the course
            if sect_seperated_json[type][course].get("L") is not None:
                # list of lecture sections
                sections.append(sect_seperated_json[type][course]["L"])
            if sect_seperated_json[type][course].get("P") is not None:
                # list of practical sections
                sections.append(sect_seperated_json[type][course]["P"])
            if sect_seperated_json[type][course].get("T") is not None:
                # list of tutorial sections
                sections.append(sect_seperated_json[type][course]["T"])
            # generate all possible combinations of sections (exhaustive and inclusive of clashes)
            combs[type][course] = list(product(*sections))
    return combs


def generate_exhaustive_timetables(
    sect_seperated_json: Annotated[
        dict, "filtered json with courses seperated into sections"
    ],
    n_dels: Annotated[int, "number of DELs selected"],
    n_opels: Annotated[int, "number of OPELs selected"],
    n_huels: Annotated[int, "number of HUELs selected"],
) -> list:
    """
    Function that generates all possible timetables (exhaustive and inclusive of clashes)

    Args:
        filtered_json (dict): filtered json file, i.e, with only courses selected

    Returns:
        list: list of all possible timetables (exhaustive and inclusive of clashes)
    """

    combs = generate_intra_combinations(sect_seperated_json)
    timetables = []
    cdcs = []
    dels = []
    opels = []
    huels = []
    for type in combs:
        for course in combs[type]:
            # format (course, section combination for that course)
            if type == "CDCs":
                cdcs.append([(str(course), comb) for comb in combs[type][course]])
            elif type == "DEls":
                dels.append([(str(course), comb) for comb in combs[type][course]])
            elif type == "OPELs":
                opels.append([(str(course), comb) for comb in combs[type][course]])
            elif type == "HUELs":
                huels.append([(str(course), comb) for comb in combs[type][course]])
            else:
                raise Exception("Course type not found in any category")

    # choose n_dels from dels
    if dels:
        dels = list(combinations(dels, n_dels))
        dels = [[j[0] for j in i] for i in dels]
    if huels:
        huels = list(combinations(huels, n_huels))
        huels = [[j[0] for j in i] for i in huels]
    if opels:
        opels = list(combinations(opels, n_opels))
        opels = [[j[0] for j in i] for i in opels]

    required = [dels, huels, opels]
    required = [i for i in required if i]
    possible_combinations_temp = list(product(*required))
    possible_combinations = []
    for i in possible_combinations_temp:
        combination = []
        for j in i:
            combination.extend(j)
        possible_combinations.append(combination)
    courses = []

    for comb in possible_combinations:
        poss = []
        poss.extend(cdcs)
        poss.extend([[c] for c in comb])
        courses.append(poss)

    timetables = list(product(*courses))
    timetables = []
    for i in range(len(courses)):
        timetables.extend(list(product(*courses[i])))
    return timetables

    # timetables = list(product(cdcs, dels, huels, opels))
    # return timetables


def remove_clashes(
    timetables: Annotated[list, "exhaustive list of all possible timetables"],
    json: Annotated[dict, "filtered json file"],
) -> list:
    """
    Function that filters out timetables with clashes

    Args:
        timetables (list): exhaustive list of all possible timetables
        json (dict): filtered json file

    Returns:
        list: list of timetables without clashes
    """
    filtered = []
    for timetable in timetables:
        # times currently held as "in use" by some course's section
        # format "DH" where D is the day and H is the hour
        times: dict[str, bool] = dict()
        clashes = False
        for course in timetable:
            course_code, sections_chosen = course

            # find out which class the course belongs to and
            # get all sections of the course
            for course_class in ["CDCs", "DEls", "HUELs", "OPELs"]:
                if course_code in json[course_class]:
                    all_sections = json[course_class][course_code]["sections"]
                    break
            else:
                raise Exception("Course code not found in any category")

            for sec in sections_chosen:
                sched = all_sections[sec]["schedule"]

                # ts denotes all slots needed for the section
                ts = []
                for i in range(len(sched)):
                    ts.extend(list(product(sched[i]["days"], sched[i]["hours"])))

                # converting it to the string of required format "DH"
                ts = [str(t[0]) + str(t[1]) for t in ts]

                # if any slot in ts is already in times, then there is a clash
                # if so, mark it as clashes and dont add it to the filtered list
                for t in ts:
                    if times.get(t) is not None:
                        clashes = True
                        break
                    else:
                        times[t] = True

                if clashes:
                    break
            if clashes:
                break

        # if no clashes, add it to the filtered list
        if not clashes:
            filtered.append(timetable)

    return filtered


def remove_exam_clashes(
    timetables: Annotated[list, "list of timetables without any clashes (classes)"],
    json: Annotated[dict, "filtered json file"],
):
    """
    Function that filters out timetables with exam clashes.

    Args:
        timetables (list): list of timetables without any clashes (classes)
        json (dict): filtered json file

    Returns:
        list: list of timetables without any clashes (classes and exams)
    """
    no_exam_clashes = []
    for timetable in timetables:
        mids_times: dict[str, int] = dict()
        compres_times: dict[str, int] = dict()
        clashes = False
        for course in timetable:
            course_code, _ = course

            # get from the json
            for course_class in ["CDCs", "DEls", "HUELs", "OPELs"]:
                if course_code in json[course_class]:
                    exams_times = json[course_class][course_code]["exams"][0]
                    break
            else:
                raise Exception("Course code not found in any category")

            mid = exams_times.get("midsem", "")
            compre = exams_times.get("compre", "")

            mids_times[mid] = mids_times.get(mid, 0) + 1
            compres_times[compre] = compres_times.get(compre, 0) + 1

        # see if more than one course has the same exam time
        for time in mids_times:
            if mids_times[time] > 1 and time is not None:
                clashes = True
                break
        if not clashes:
            for time in compres_times:
                if compres_times[time] > 1 and time is not None:
                    clashes = True
                    break

        # for i in range(len(mids_times)):
        #     for j in range(i + 1, len(mids_times)):
        #         if mids_times[i] == mids_times[j]:
        #             clashes = True
        #             break
        #     if clashes:
        #         break
        # if not clashes:
        #     for i in range(len(compres_times)):
        #         for j in range(i + 1, len(compres_times)):
        #             if compres_times[i] == compres_times[j]:
        #                 clashes = True
        #                 break
        #         if clashes:
        #             break
        # add to filtered list only if no clashes
        if not clashes:
            no_exam_clashes.append(timetable)
    return no_exam_clashes


def get_daywise_schedule(
    cf_timetable: Annotated[list, "timetable without clashes"],
    json: Annotated[dict, "filtered json file"],
):
    """
    Returns dictionary containing the hour numbers (1 -> 8-9AM etc)
    of classes for each weekday for the provided timetable

    the timetable must not have any clashes.

    Args:
        cf_timetable (list[tuple]): timetable without clashes
        json (dict): filtered json file, i.e, with only courses selected
    """

    schedule = {day: list() for day in DAYS}

    for course in cf_timetable:
        course_code, sections_chosen = course
        # get from the json
        for course_class in ["CDCs", "DEls", "HUELs", "OPELs"]:
            if course_code in json[course_class]:
                all_sections = json[course_class][course_code]["sections"]
                break
        else:
            raise Exception("Course code not found in any category")

        for sec in sections_chosen:
            sched = all_sections[sec]["schedule"]
            # since no clashes, we can just append the hours to the schedule
            for i in range(len(sched)):
                for day in sched[i]["days"]:
                    schedule[day].append(sched[i]["hours"])

    return schedule


def sort_acc_to_heuristics(
    timetables: Annotated[list, "list of timetables without clashes"],
    json: Annotated[dict, "filtered json file"],
    free_days: Annotated[list[str], "list of days to be free if possible"],
    lite_order: Annotated[
        list[str],
        "increasing order of how lite you want days to be (earlier means more lite)",
    ],
    exam_fit_strategy: Optional[str] = None,
    filter_exams_on_same_day=False,
    filter: Annotated[bool, "whether to filter or to just sort"] = False,
    strong: Annotated[bool, "whether to use strong filter or not"] = False,
) -> list:
    """
    Function that will sort all timetables based on whether the timetable
    matches free days, the lite order, the total number of free days, and
    exam fit strategy, and whether to filter exams on same day.

    Note:
      exam fit strategy, if specified, can be "Close Together" or "Spaced Apart".

      Lite order is the order in which you want the days to be lite. For example, if you want Saturday to be the most lite day, then lite_order = ["S", "Su", "M", "T", "W", "Th", "F"] (set the order of the other 6 accordingly)

    Args:
        timetables (list): list of timetables without clashes
        json (dict): filtered json file, i.e, with only courses selected
        free_days (list): list of days to be free if possible
        lite_order (list): increasing order of how lite you want days to be (earlier means more lite)
        exam_fit_strategy (str, optional): the strategy to use to sort exam spread seconds
        filter_exams_on_same_day (bool): whether to reduce rank of timetables which have exams on same day
        filter (bool, optional): whether to filter or to just sort. Defaults to False.
        strong (bool, optional): whether to use strong filter or not. Defaults to False.

    Returns:
        list: list of timetables after sorting.
    """

    # sort order mask is a multiplier mask whose elements act on heuristic to
    # determine ordering
    day_dict = {day: i for i, day in enumerate(DAYS)}
    result_list = []

    sort_order_mask = [
        1,  # does_match_free_days -> ascending
        1,  # daily_scores -> ascending
        -1,  # n_free -> descending
    ]

    exam_spread_handler = ExamSpread(json)

    if filter_exams_on_same_day:
        sort_order_mask.append(-1)  # timetables which have a clash are ranked lower

    if exam_fit_strategy is not None:
        assert exam_fit_strategy in EXAM_FIT_STRATEGIES
        # ascending or descending based on which strategy is chosen
        sort_order_mask.append(EXAM_FIT_STRATEGIES[exam_fit_strategy])

    def get_sort_key(decorated_tt):
        heuristics, _ = decorated_tt
        return tuple(
            [
                multiplier * heuristic
                for multiplier, heuristic in zip(sort_order_mask, heuristics)
            ]
        )

    for timetable in timetables:
        # will contain the hours of each day where there is a class.
        # used for calculating the daily scores and if it matches the free days
        schedule = get_daywise_schedule(timetable, json)
        heuristics = []

        # --- append heuristics in the order of their priority ---

        # calulate number of free days
        n_free = 0
        for day in free_days:
            if len(schedule[day]) == 0:
                n_free += 1

        does_match_free_days = (n_free > 0 and not strong) or n_free == len(free_days)
        if filter and not does_match_free_days:
            continue

        heuristics.append(does_match_free_days)

        # calculating the daily scores and reordering them acc to lite order
        daily_scores = [len(schedule[day]) for day in DAYS]
        daily_scores = [daily_scores[day_dict[day]] for day in lite_order]

        heuristics.append(daily_scores)
        heuristics.append(n_free)

        total_spread_seconds, exam_on_same_day = exam_spread_handler.compute(timetable)

        if filter_exams_on_same_day:
            heuristics.append(exam_on_same_day)

        if exam_fit_strategy is not None:
            heuristics.append(total_spread_seconds)

        # decorate timetable with the heuristics
        decorated_tt = (
            tuple(heuristics),
            timetable,
        )
        result_list.append(decorated_tt)

    result_list = sorted(result_list, key=get_sort_key)

    lite_order_index = {day: i for i, day in enumerate(lite_order)}

    # reorder the daily scores back to Monday to Friday
    for i in range(len(result_list)):
        heuristics, timetable = result_list[i]
        before, daily_scores, *after = heuristics
        daily_scores = [daily_scores[lite_order_index[day]] for day in DAYS]
        heuristics = tuple([before, daily_scores, *after])
        result_list[i] = (heuristics, timetable)

    return result_list


def export_to_json(timetables: list, filtered_json: dict, n_export: int = 100) -> None:
    """
    Function that exports your timetables to a json file (in the sorted order)

    Args:
        timetables (list): list of timetables
        filtered_json (dict): filtered json file, i.e, with only courses selected
        n_export (int, optional): number of timetables to export. Defaults to 100.

    Returns:
        None
    """
    export = []
    for (_, daily_scores, n_free, *_), timetable in timetables:
        export_tt = {}
        export_tt["free_matched"] = n_free
        export_tt["daily_scores"] = daily_scores
        export_tt["timetable"] = {}
        for course in timetable:
            export_tt["timetable"][course[0]] = {}
            export_tt["timetable"][course[0]]["sections"] = {}
            for sec in course[1]:
                export_tt["timetable"][course[0]]["sections"][sec] = {}
                export_tt["timetable"][course[0]]["sections"][sec]["schedule"] = []
                if course[0] in filtered_json["CDCs"]:
                    sched = filtered_json["CDCs"][course[0]]["sections"][sec][
                        "schedule"
                    ]
                elif course[0] in filtered_json["DEls"]:
                    sched = filtered_json["DEls"][course[0]]["sections"][sec][
                        "schedule"
                    ]
                elif course[0] in filtered_json["HUELs"]:
                    sched = filtered_json["HUELs"][course[0]]["sections"][sec][
                        "schedule"
                    ]
                elif course[0] in filtered_json["OPELs"]:
                    sched = filtered_json["OPELs"][course[0]]["sections"][sec][
                        "schedule"
                    ]
                else:
                    raise Exception("Course code not found in any category")
                for i in range(len(sched)):
                    export_tt["timetable"][course[0]]["sections"][sec][
                        "schedule"
                    ].append(
                        {
                            "days": sched[i]["days"],
                            "hours": sched[i]["hours"],
                        }
                    )
            if course[0] in filtered_json["CDCs"]:
                exam = filtered_json["CDCs"][course[0]]["exams"][0]
            elif course[0] in filtered_json["DEls"]:
                exam = filtered_json["DEls"][course[0]]["exams"][0]
            elif course[0] in filtered_json["HUELs"]:
                exam = filtered_json["HUELs"][course[0]]["exams"][0]
            elif course[0] in filtered_json["OPELs"]:
                exam = filtered_json["OPELs"][course[0]]["exams"][0]
            else:
                raise Exception("Course code not found in any category")
            export_tt["timetable"][course[0]]["exams"] = exam
        export.append(export_tt)
        if len(export) == n_export:
            break
    json.dump(export, open("./files/my_timetables.json", "w"), indent=4)


def get_excluded_section_choices(sect_seperated_json):
    """
    function returns list of choices objects for every section of every course
    in which each choice object returns the index of the section as a tuple

    Args:
        sect_seperated_json: filtered json in which sections
          of each course are sepererated into course types
          with nested index of the form (course_class, course_name,
          section_type, section)
    """
    section_exclude_choices = []
    # create a choice object for every section of every course
    # which will be used for fuzzy selecting
    for course_class, courses in sect_seperated_json.items():
        for course_name, course_dict in courses.items():
            for section_type, sections in course_dict.items():
                for section in sections:
                    # the fuzzy selector will return this kind of index tuple (to index into
                    # sect_seperated_json) for each of the courses
                    # the user wishes to exclude
                    excluded_section_info = (
                        (course_class, course_name, section_type),
                        section,
                    )
                    section_exclude_choices.append(
                        Choice(
                            # this is the actual value that is added to the selection list
                            excluded_section_info,
                            # this value is shown to the user for selection
                            name=f"{course_name} - {section}",
                        )
                    )
    return section_exclude_choices


if __name__ == "__main__":
    tt_json = json.load(open("./files/timetable.json", "r"))

    # has to be a list since dict_keys is not pickelable for prompt tools
    possible_courses = list(tt_json["courses"].keys())
    CDC, *electives = AskUserInput.course_info(possible_courses)

    nDels, nOpels, nHuels = AskUserInput.ask_number_of_each_elective(
        [len(courses_per_type) for courses_per_type in electives]
    )

    (lite_order, free_days) = AskUserInput.work_load_spread()
    pref = ["DEls", "OPELs", "HUELs"]  # unused why is this here?

    DEls, HUELs, OPELs = electives
    filtered_json = get_filtered_json(tt_json, CDC, DEls, HUELs, OPELs)
    sect_seperated_json = separate_sections_into_types(filtered_json)

    excluded_sections = AskUserInput.get_excluded_sections(
        get_excluded_section_choices(sect_seperated_json),
        sect_seperated_json,
    )

    # remove all excluded sections
    for (course_class, course_name, section_type), section in excluded_sections:
        sect_seperated_json[course_class][course_name][section_type].remove(section)

    exam_fit_strategy = AskUserInput.fuzzy_select(
        "How do you want your exam schedule to be",
        list(EXAM_FIT_STRATEGIES.keys()),
        multiselect=False,
        default="NONE",
    )

    filter_exams_on_same_day = AskUserInput.ask_bool(
        "should exams on same day be filtered?", default=False
    )

    exhaustive_list_of_timetables = generate_exhaustive_timetables(
        sect_seperated_json, nDels, nOpels, nHuels
    )

    timetables_without_clashes = remove_clashes(
        exhaustive_list_of_timetables, filtered_json
    )

    print(
        "Number of timetables without clashes (classes):",
        len(timetables_without_clashes),
    )

    timetables_without_clashes = remove_exam_clashes(
        timetables_without_clashes, filtered_json
    )

    print(
        "Number of timetables without clashes (classes and exams):",
        len(timetables_without_clashes),
    )

    in_my_preference_order = sort_acc_to_heuristics(
        timetables_without_clashes,
        filtered_json,
        free_days,
        lite_order,
        exam_fit_strategy,
        filter_exams_on_same_day,
        filter=False,
        strong=False,
    )

    print("Number of timetables after filter: ", len(in_my_preference_order))

    if len(in_my_preference_order) > 0:
        print(
            "-----------------------------------------------------",
            "\nHighest match:\n",
            in_my_preference_order[0],
            "\n\n",
            "-----------------------------------------------------",
            "\nLowest match:\n",
            in_my_preference_order[-1],
        )
    else:
        print("No timetables found")

    export_to_json(in_my_preference_order, filtered_json)
