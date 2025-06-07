from random import choice

import pygame
import pygame_gui
import os
import platform
import subprocess
import ujson

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.pelts import Pelt
from scripts.cat.personality import Personality
from scripts.cat.skills import SkillPath, Skill
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton, UIModifiedScrollingContainer, UITextBoxTweaked, \
    UICheckbox, UIModifiedImage, UIScrollingButtonList, UIDropDown, \
    UICollapsibleContainer, UIScrollingDropDown
from scripts.screens.RelationshipScreen import RelationshipScreen
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.icon import Icon
from scripts.utility import ui_scale, process_text, ui_scale_dimensions


class EventEdit(Screens):
    """
    This screen provides an interface to allow devs to edit and create events.
    """
    preview_states = ("off", 1, 2)
    test_cat_names = {
        "m_c": "MainCat",
        "r_c": "RandomCat",
        "n_c:1": "NewCat",
        "mur_c": "MurderedCat",
        "lead_name": "TestStar",
        "dep_name": "DepCat",
        "med_name": "MedCat"
    }
    test_pronouns = [
        {
            "subject": "they",
            "object": "them",
            "poss": "their",
            "inposs": "theirs",
            "self": "themself",
            "conju": 1
        },
        {
            "subject": "she",
            "object": "her",
            "poss": "her",
            "inposs": "hers",
            "self": "herself",
            "conju": 2
        },
        {
            "subject": "he",
            "object": "him",
            "poss": "his",
            "inposs": "his",
            "self": "himself",
            "conju": 2
        }
    ]

    all_camps = {
        "Forest": ["Classic", "Gully", "Grotto", "Lakeside"],
        "Mountainous": ["Cliff", "Cavern", "Crystal River", "Ruins"],
        "Plains": ["Grasslands", "Tunnels", "Wastelands"],
        "Beach": ["Tidepools", "Tidal Cave", "Shipwreck", "Fjord"]
    }
    all_seasons = ("newleaf", "greenleaf", "leaf-fall", "leaf-bare")

    event_types = {
        "death": ["murder", "old_age", "mass_death", "war"],
        "injury": ["war"],
        "misc": ["murder_reveal", "accessory", "ceremony", "war"],
        "new_cat": ["war"]
    }

    # TODO: consider moving some of these into a file that facilitates new additions
    basic_tag_list = [
        {
            "tag": "classic",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "cruel_season",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "no_body",
            "setting": False,
            "required_type": "death",
            "conflict": None
        },
        {
            "tag": "clan_wide",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "romance",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "adoption",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "all_lives",
            "setting": False,
            "required_type": "death",
            "conflict": ["some_lives", "lives_remain"]
        },
        {
            "tag": "some_lives",
            "setting": False,
            "required_type": "death",
            "conflict": ["all_lives"]
        },
        {
            "tag": "lives_remain",
            "setting": False,
            "required_type": "death",
            "conflict": ["all_lives"]
        },
        {
            "tag": "high_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["mid_lives", "low_lives"]
        },
        {
            "tag": "mid_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["high_lives", "low_lives"]
        },
        {
            "tag": "low_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["mid_lives", "high_lives"]
        }
    ]

    rel_tag_list = [
        {
            "tag": "siblings",
            "setting": False,
            "conflict": ["mates",
                         "not_mates",
                         "parent/child",
                         "child/parent"]
        },
        {
            "tag": "mates",
            "setting": False,
            "conflict": ["siblings",
                         "parent/child",
                         "child/parent",
                         "app/mentor",
                         "mentor/app",
                         "not_mates"]
        },
        {
            "tag": "not_mates",
            "setting": False,
            "conflict": ["siblings",
                         "mates",
                         "parent/child",
                         "child/parent",
                         "app/mentor",
                         "mentor/app"]
        },
        {
            "tag": "parent/child",
            "setting": False,
            "conflict": ["siblings",
                         "mates",
                         "not_mates",
                         "child/parent",
                         "app/mentor"]
        },
        {
            "tag": "child/parent",
            "setting": False,
            "conflict": ["siblings",
                         "mates",
                         "not_mates",
                         "parent/child",
                         "mentor/app"]
        },
        {
            "tag": "app/mentor",
            "setting": False,
            "conflict": ["mates",
                         "not_mates",
                         "parent/child",
                         "mentor/app"]
        },
        {
            "tag": "mentor/app",
            "setting": False,
            "conflict": ["mates",
                         "not_mates",
                         "child/parent",
                         "app/mentor"]
        }
    ]
    rel_value_types = RelationshipScreen.rel_value_names

    all_ranks = Cat.rank_sort_order.copy()
    all_ranks.reverse()

    all_ages = [age.value for age in Cat.age_moons.keys()]
    all_ages.reverse()

    all_skills = {k: v for (k, v) in zip([path.name for path in SkillPath], [path.value for path in SkillPath])}

    adult_traits = Personality.trait_ranges["normal_traits"].keys()
    kit_traits = Personality.trait_ranges["kit_traits"].keys()

    all_backstories = BACKSTORIES["backstory_categories"]
    individual_stories = []
    for pool in all_backstories:
        individual_stories.extend(all_backstories[pool])

    new_cat_types = ["kittypet", "loner", "rogue", "clancat"]

    new_cat_bools = [
        {
            "tag": "litter",
            "setting": False,
            "conflict": ["exists", "new_name", "old_name"]
        },
        {
            "tag": "meeting",
            "setting": False,
            "conflict": ["old_name", "new_name"]
        },
        {
            "tag": "exists",
            "setting": False,
            "conflict": ["litter"]
        },
        {
            "tag": "new_name",
            "setting": False,
            "conflict": ["old_name", "litter", "meeting"]
        },
        {
            "tag": "old_name",
            "setting": False,
            "conflict": ["new_name", "litter", "meeting"]
        },
    ]

    new_cat_ranks = all_ranks.copy()
    new_cat_ranks.remove("leader")
    new_cat_ranks.remove("deputy")

    new_cat_ages = all_ages.copy()
    new_cat_ages.extend(["has_kits", "mate"])

    new_cat_genders = ["male", "female", "can_birth"]

    section_tabs = {
        "settings": Icon.PAW,
        "main cat": Icon.CAT_HEAD,
        "random cat": Icon.CAT_HEAD,
        "new cats": Icon.CAT_HEAD,
        "personal consequences": Icon.SCRATCHES,
        "outside consequences": Icon.CLAN_UNKNOWN
    }

    def __init__(self, name=None):
        super().__init__(name)

        self.event_text_container = None
        self.editor_container = None
        self.add_button = None
        self.event_list_container = None
        self.event_list = None
        self.list_frame = None
        self.main_menu_button = None

        self.current_editor_tab = None

        self.type_tab_buttons = {}
        self.biome_tab_buttons = {}
        self.event_buttons = {}

        self.editor_element = {}

        self.event_text_element = {}

        # Settings elements
        self.event_id_element = {}

        self.location_element = {}
        self.location_info = []

        self.season_element = {}
        self.season_info = []

        self.type_element = {}
        self.type_info = ["death"]

        self.sub_element = {}
        self.sub_info = []

        self.tag_element = {}
        self.basic_tag_checkbox = {}
        self.rank_tag_checkbox = {}
        self.tag_info = []

        self.weight_element = {}
        self.weight_info = 20

        self.acc_element = {}
        self.acc_info = []
        self.acc_categories = Pelt.acc_categories
        self.open_category = None
        self.acc_button = {}

        self.main_cat_editor = {}
        self.random_cat_editor = {}

        self.death_element = {}
        self.rank_element = {}
        self.age_element = {}

        self.rel_status_element = {}
        self.rel_status_checkbox = {}
        self.rel_value_element = {}

        self.skill_element = {}
        self.level_element = {}
        self.skill_allowed = True
        self.open_path = None
        self.chosen_level = None

        self.trait_element = {}
        self.trait_allowed = True

        self.backstory_element = {}
        self.open_pool = None

        self.main_cat_info = {
            "rank": [],
            "age": [],
            "rel_status": [],
            "dies": False,
            "skill": [],
            "not_skill": [],
            "trait": [],
            "not_trait": [],
            "backstory": []
        }
        # TODO: add a checkbox somewhere that indicates if the event should have a random cat
        self.random_cat_info = {
            "rank": [],
            "age": [],
            "rel_status": [],
            "dies": False,
            "skill": [],
            "not_skill": [],
            "trait": [],
            "not_trait": [],
            "backstory": []
        }
        self.new_cat_info_dict = {}
        self.new_cat_info = {
            "backstory": [],
            "parent": [],
            "adoptive": [],
            "mate": []
        }

        self.current_cat_dict = self.main_cat_info

        self.new_cat_editor = {}
        self.new_cat_element = {}
        self.new_cat_list = {}
        self.selected_new_cat = None

        self.new_cat_checkbox = {}
        self.cat_story_element = {}
        self.new_status_element = {}
        self.new_age_element = {}
        self.new_gender_element = {}
        self.connections_element = {}
        self.open_connection = "parent"

        self.chosen_type = None
        self.chosen_biome = None
        self.chosen_event = None

        self.current_preview_state = self.preview_states[0]

        self.new_event = {}

    def handle_event(self, event):
        # HANDLE TEXT LINKS
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-u", event.link_target])
            elif platform.system() == "Windows":
                os.system(f'start "" {event.link_target}')
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", event.link_target])

        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            # MAIN MENU RETURN
            if event.ui_element == self.main_menu_button:
                self.change_screen("start screen")
                return

            # SELECT TYPE
            elif event.ui_element in self.type_tab_buttons.values():
                for tab in self.type_tab_buttons:
                    if event.ui_element == self.type_tab_buttons[tab]:
                        self.chosen_type = tab
                        break

                self.select_biome_tab_creation()

            # SELECT BIOME
            elif event.ui_element in self.biome_tab_buttons.values():
                if event.ui_element == self.biome_tab_buttons["back"]:
                    self.select_type_tab_creation()
                    self.event_list = None

                else:
                    for tab in self.biome_tab_buttons:
                        if event.ui_element == self.biome_tab_buttons[tab]:
                            self.chosen_biome = tab.capitalize() if tab != "general" else tab
                            break

                    self.display_events()

            # SELECT EVENT
            elif event.ui_element in self.event_buttons.values():
                self.chosen_event = event.ui_element.text

            # OPEN EDITOR
            elif event.ui_element == self.add_button:
                # TODO: need confirmation window for clicking after editor is already open
                # TODO: as well as a proper func to clear info
                if not self.event_id_element.get("event_id_text"):
                    self.chosen_event = None
                    self.display_editor()

            # SWITCH EDITOR TAB
            elif event.ui_element in self.editor_element.values():
                for name, button in self.editor_element.items():
                    if event.ui_element == button and name != self.current_editor_tab:
                        self.current_editor_tab = name
                        self.clear_editor_tab()
                        break

            # SETTINGS TAB EVENTS
            elif self.current_editor_tab == "settings":
                self.handle_settings_events(event)

            # MAIN/RANDOM CAT TAB EVENTS
            elif self.current_editor_tab in ["main cat", "random cat"]:
                self.handle_main_and_random_cat_events(event)

            # NEW CAT TAB EVENTS
            # ADD CAT
            elif self.current_editor_tab == "new cats":
                self.handle_new_cat_events(event)

        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            # CHANGE EVENT ID
            if event.ui_element == self.event_id_element.get("event_id_entry"):
                self.new_event.update({"event_id": self.event_id_element["event_id_entry"].text})

            elif event.ui_element in self.rel_value_element.values():
                info = self.current_cat_dict["rel_status"]
                for value, element in self.rel_value_element.items():
                    value = value.replace('_entry', '')
                    if element != event.ui_element:
                        continue
                    remove_tag = None
                    for tag in info:
                        if value in tag:
                            remove_tag = tag
                            break
                    if remove_tag:
                        info.remove(remove_tag)
                    if element.text:
                        self.current_cat_dict["rel_status"].append(f"{value}_{element.text}")
                    self.update_rel_status_info()
                    break

    def handle_new_cat_events(self, event):
        # ADD CAT
        if event.ui_element == self.new_cat_editor["add"]:
            new_index = len(self.new_cat_list) if self.new_cat_list else 0
            self.selected_new_cat = f"n_c:{new_index}"
            self.change_new_cat_info_dict()
            self.new_cat_list[self.selected_new_cat] = []
            self.new_cat_editor["cat_list"].new_item_list(self.new_cat_list.keys())
            self.new_cat_editor["cat_list"].set_selected_list([self.selected_new_cat])
            self.new_cat_editor["info"].set_text(f"selected cat: []")
            if self.new_cat_element.get("checkbox_container"):
                self.update_new_cat_options()

        # DELETE CAT
        elif event.ui_element == self.new_cat_editor["delete"] and self.selected_new_cat:
            # retain needed info then clear new_cat_list
            deleted = self.selected_new_cat
            self.new_cat_list.pop(deleted)
            self.new_cat_info_dict.pop(deleted)
            old_list = self.new_cat_list.copy()
            self.new_cat_list.clear()

            # create new cat list
            for index, cat in enumerate(old_list.values()):
                self.new_cat_list[f"n_c:{index}"] = cat

            self.new_cat_editor["cat_list"].new_item_list(self.new_cat_list.keys())

            self.selected_new_cat = list(self.new_cat_list.keys())[-1] if self.new_cat_list.keys() else None

            if self.selected_new_cat:
                self.new_cat_editor["cat_list"].set_selected_list([self.selected_new_cat])
                self.new_cat_editor["info"].set_text(
                    f"selected cat: {self.new_cat_list.get(self.selected_new_cat) if self.new_cat_list.get(self.selected_new_cat) else '[]'}")
                self.change_new_cat_info_dict()

            else:
                self.new_cat_editor["info"].set_text("No cat selected")

            self.update_new_cat_options()

        # CHECKBOXES
        elif event.ui_element in self.new_cat_checkbox.values():
            event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
            for info in self.new_cat_bools:
                if event.ui_element == self.new_cat_checkbox.get(info["tag"]):
                    index = self.new_cat_bools.index(info)
                    self.new_cat_bools[index] = {
                        "tag": info["tag"],
                        "setting": False if info["setting"] else True,
                        "conflict": info["conflict"]
                    }

                    # flip the setting of any conflicting tags
                    if info["conflict"]:
                        for tag in info["conflict"]:
                            conflict_info = [block for block in self.new_cat_bools if tag == block["tag"]][0]
                            conflict_index = self.new_cat_bools.index(conflict_info)
                            if not info["setting"]:  # unchecks if conflicted setting is checked
                                self.new_cat_checkbox[tag].uncheck()
                            self.new_cat_bools[conflict_index] = {
                                "tag": conflict_info["tag"],
                                "setting": False,
                                "conflict": conflict_info["conflict"]
                            }
                    self.update_new_cat_tags()
                    break

        # CONNECTIONS
        elif event.ui_element == self.connections_element["birth_parent"]:
            self.open_connection = "parent"
            self.connections_element["birth_parent"].disable()
            self.connections_element["adopt_parent"].enable()
            self.connections_element["mate"].enable()

            self.connections_element["text"].set_text("screens.event_edit.new_cat_parent_info")
            self.editor_container.on_contained_elements_changed(self.connections_element["text"])
            self.connections_element["info"].set_text(f"chosen cats: {self.new_cat_info['parent']}")

            self.connections_element["cat_list"].set_selected_list(self.new_cat_info["parent"].copy())
            used_cats = self.new_cat_info["adoptive"] + self.new_cat_info["mate"]
            for cat, button in self.connections_element["cat_list"].buttons.items():
                if cat in used_cats:
                    button.disable()
                else:
                    button.enable()

        elif event.ui_element == self.connections_element["adopt_parent"]:
            self.open_connection = "adoptive"
            self.connections_element["birth_parent"].enable()
            self.connections_element["adopt_parent"].disable()
            self.connections_element["mate"].enable()

            self.connections_element["text"].set_text("screens.event_edit.new_cat_adoptive_info")
            self.editor_container.on_contained_elements_changed(self.connections_element["text"])
            self.connections_element["info"].set_text(f"chosen cats: {self.new_cat_info['adoptive']}")

            self.connections_element["cat_list"].set_selected_list(self.new_cat_info["adoptive"].copy())
            used_cats = self.new_cat_info["parent"] + self.new_cat_info["mate"]
            for cat, button in self.connections_element["cat_list"].buttons.items():
                if cat in used_cats:
                    button.disable()
                else:
                    button.enable()
        elif event.ui_element == self.connections_element["mate"]:
            self.open_connection = "mate"
            self.connections_element["birth_parent"].enable()
            self.connections_element["adopt_parent"].enable()
            self.connections_element["mate"].disable()

            self.connections_element["text"].set_text("screens.event_edit.new_cat_mate_info")
            self.editor_container.on_contained_elements_changed(self.connections_element["text"])
            self.connections_element["info"].set_text(f"chosen cats: {self.new_cat_info['mate']}")

            self.connections_element["cat_list"].set_selected_list(self.new_cat_info["mate"].copy())
            used_cats = self.new_cat_info["adoptive"] + self.new_cat_info["parent"]
            for cat, button in self.connections_element["cat_list"].buttons.items():
                if cat in used_cats:
                    button.disable()
                else:
                    button.enable()
        else:
            self.handle_main_and_random_cat_events(event)
            self.update_new_cat_tags()

    def handle_main_and_random_cat_events(self, event):
        # DIES
        if event.ui_element == self.death_element.get("checkbox"):
            checked = event.ui_element.checked
            if not checked:
                event.ui_element.check()
            else:
                event.ui_element.uncheck()
            self.current_cat_dict["dies"] = event.ui_element.checked
            self.death_element["info"].set_text(f"dies: {event.ui_element.checked}")

        # REL STATUS CHECKBOXES
        elif event.ui_element in self.rel_status_checkbox.values():
            event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
            for info in self.rel_tag_list:
                if event.ui_element == self.rel_status_checkbox.get(info["tag"]):
                    index = self.rel_tag_list.index(info)
                    self.rel_tag_list[index] = {
                        "tag": info["tag"],
                        "setting": False if info["setting"] else True,
                        "conflict": info["conflict"]
                    }

                    # flip the setting of any conflicting tags
                    if info["conflict"]:
                        for tag in info["conflict"]:
                            conflict_info = [block for block in self.rel_tag_list if tag == block["tag"]][0]
                            conflict_index = self.rel_tag_list.index(conflict_info)
                            if not info["setting"]:  # unchecks if conflicted setting is checked
                                self.rel_status_checkbox[tag].uncheck()
                            self.rel_tag_list[conflict_index] = {
                                "tag": conflict_info["tag"],
                                "setting": False,
                                "conflict": conflict_info["conflict"]
                            }

                    self.update_rel_status_info()
                    break
        # REL VALUE BUTTONS
        elif event.ui_element in self.rel_value_element.values():
            for name, button in self.rel_value_element.items():
                if button != event.ui_element:
                    continue
                amount = 0
                value = name
                if "low" in name:
                    value = name.replace("_low_button", "")
                    amount = 10
                elif "mid" in name:
                    value = name.replace("_mid_button", "")
                    amount = 30
                elif "high" in name:
                    value = name.replace("_high_button", "")
                    amount = 50

                # removing tag if it's already present
                remove_tag = None
                for tag in self.current_cat_dict["rel_status"]:
                    if value in tag:
                        remove_tag = tag
                        break
                if remove_tag:
                    self.current_cat_dict["rel_status"].remove(remove_tag)

                self.current_cat_dict["rel_status"].append(f"{value}_{amount}")
                self.rel_value_element[f"{value}_entry"].set_text(str(amount))
                self.update_rel_status_info()

        # SKILL TOGGLE
        elif event.ui_element == self.skill_element.get("allow"):
            self.skill_element["allow"].disable()
            self.skill_element["exclude"].enable()
            self.skill_allowed = True
        elif event.ui_element == self.skill_element.get("exclude"):
            self.skill_element["exclude"].disable()
            self.skill_element["allow"].enable()
            self.skill_allowed = False
        # SKILL LEVELS
        elif event.ui_element in self.level_element.values():
            for name, button in self.level_element.items():
                if button != event.ui_element:
                    continue
                self.chosen_level = name
                self.update_skill_info()
                break

        # TRAIT TOGGLE
        elif event.ui_element == self.trait_element.get("allow"):
            self.trait_element["allow"].disable()
            self.trait_element["exclude"].enable()
            self.trait_allowed = True
            # reset selected list
            self.trait_element["adult"].set_selected_list(
                list(set(self.current_cat_dict["trait"]).intersection(self.adult_traits)))
            self.trait_element["kitten"].set_selected_list(
                list(set(self.current_cat_dict["trait"]).intersection(self.kit_traits)))

        elif event.ui_element == self.trait_element.get("exclude"):
            self.trait_element["exclude"].disable()
            self.trait_element["allow"].enable()
            self.trait_allowed = False
            # reset selected list
            self.trait_element["adult"].set_selected_list(
                list(set(self.current_cat_dict["not_trait"]).intersection(self.adult_traits)))
            self.trait_element["kitten"].set_selected_list(
                list(set(self.current_cat_dict["not_trait"]).intersection(self.kit_traits)))

        # BACKSTORY LIST
        elif event.ui_element in (self.backstory_element.get("list").buttons.values()
        if self.backstory_element.get("list") else []):
            for name, button in self.backstory_element["list"].buttons.items():
                if button != event.ui_element:
                    continue
                chosen_stories = self.current_cat_dict["backstory"]

                if name in chosen_stories:
                    chosen_stories.remove(name)
                    if not set(chosen_stories).intersection(self.backstory_element["list"].selected_list):
                        chosen_stories.append(self.open_pool)
                else:
                    chosen_stories.append(name)
                    if self.open_pool in chosen_stories:
                        chosen_stories.remove(self.open_pool)
                self.update_backstory_info()
                break

    def handle_settings_events(self, event):
        # TEXT PREVIEW
        if event.ui_element == self.event_text_element["preview_button"]:
            # finds what the new preview state should be
            index = self.preview_states.index(self.current_preview_state)
            new_index = index + 1 if index + 1 <= 2 else 0
            self.current_preview_state = self.preview_states[new_index]

            # switches states
            if new_index == 0:
                self.event_text_element["event_text"].show()
                self.event_text_element["preview_text"].hide()
            else:
                self.event_text_element["event_text"].hide()
                text = self.event_text_element["event_text"].html_text

                test_dict = {}
                for abbr in self.test_cat_names:
                    pronoun = choice(
                        [pro for pro in self.test_pronouns if pro["conju"] == self.current_preview_state]
                    )
                    test_dict[abbr] = (
                        self.test_cat_names[abbr], pronoun
                    )

                text = process_text(text, test_dict)
                self.event_text_element["preview_text"].set_text(text)
                self.event_text_element["preview_text"].show()

        # CHANGE LOCATION LIST
        if event.ui_element in self.location_element.values():
            biome_list = game.clan.BIOME_TYPES
            for biome in biome_list:
                if event.ui_element == self.location_element[biome]:
                    self.update_location_info(biome=biome)
                    break
            for camp in [camp for biome in self.all_camps.values() for camp in biome]:
                if event.ui_element == self.location_element.get(camp):
                    self.update_location_info(camp=camp)
                    break

        # CHANGE BASIC TAGS
        elif event.ui_element in self.basic_tag_checkbox.values():
            event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
            for info in self.basic_tag_list:
                if event.ui_element == self.basic_tag_checkbox.get(info["tag"]):
                    index = self.basic_tag_list.index(info)
                    self.basic_tag_list[index] = {
                        "tag": info["tag"],
                        "setting": False if info["setting"] else True,
                        "required_type": info["required_type"],
                        "conflict": info["conflict"]
                    }

                    # flip the setting of any conflicting tags
                    if info["conflict"]:
                        for tag in info["conflict"]:
                            conflict_info = [block for block in self.basic_tag_list if tag == block["tag"]][0]
                            conflict_index = self.basic_tag_list.index(conflict_info)
                            if not info["setting"]:  # unchecks if conflicted setting is checked
                                self.basic_tag_checkbox[tag].uncheck()
                            self.basic_tag_list[conflict_index] = {
                                "tag": conflict_info["tag"],
                                "setting": False,
                                "required_type": conflict_info["required_type"],
                                "conflict": conflict_info["conflict"]
                            }

                    self.update_tag_info()
                    break

        # CHANGE RANK TAGS
        elif event.ui_element in self.rank_tag_checkbox.values():
            event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
            self.update_tag_info()

        # CHANGE ACC CATEGORY
        # individual accs
        elif (self.acc_element.get("acc_display")
              and event.ui_element in self.acc_element["acc_display"].buttons.values()):
            for acc, button in self.acc_element["acc_display"].buttons.items():
                if event.ui_element != button:
                    continue
                if acc in self.acc_info:
                    self.acc_info.remove(acc)
                else:
                    self.acc_info.append(acc)
                break
            self.update_acc_info()
        # greater categories
        elif event.ui_element in self.acc_element.values():
            for group, button in self.acc_element.items():
                if event.ui_element != button:
                    continue
                if group != self.open_category:
                    self.open_category = group
                    self.update_acc_list()
                    if group not in self.acc_info:
                        self.acc_info.append(group)
                        self.replace_accs_with_group(group)
                else:
                    if group in self.acc_info:
                        self.acc_info.remove(group)
                        self.open_category = None
                        self.update_acc_list()
                    else:
                        self.replace_accs_with_group(group)
                break
            self.update_acc_info()

    def on_use(self):
        """
        We'll use this to check and update some of our custom ui_elements due to the order update() and handle_event()
        funcs run in.
        """
        if self.current_editor_tab == "settings":
            self.handle_settings_on_use()

        elif self.current_editor_tab in ["main cat", "random cat"]:
            self.handle_main_and_random_cat_on_use()

        elif self.current_editor_tab == "new cats":
            self.handle_new_cat_on_use()

        super().on_use()

    def handle_new_cat_on_use(self):
        # NEW CAT CONSTRAINT DISPLAY
        if self.selected_new_cat and not self.new_cat_element.get("checkbox_container"):
            self.display_new_cat_constraints()

        elif not self.selected_new_cat and self.new_cat_element.get("checkbox_container"):
            self.clear_new_cat_constraints()
        # CHANGE SELECTED CAT
        if self.new_cat_editor.get("cat_list"):
            new_selection = (self.new_cat_editor["cat_list"].selected_list[0]
                             if self.new_cat_editor["cat_list"].selected_list else None)
            if self.selected_new_cat != new_selection:
                self.selected_new_cat = new_selection
                self.change_new_cat_info_dict()
                self.update_new_cat_options()
                self.new_cat_editor["info"].set_text(
                    f"selected cat: "
                    f"{self.new_cat_list.get(self.selected_new_cat) if self.new_cat_list.get(self.selected_new_cat) else '[]'}")

                # need to reset the cat connections info here or it'll be incorrect
                new_selection = (self.connections_element["cat_list"].selected_list.copy()
                                 if self.connections_element["cat_list"].selected_list else [])
                self.connections_element["info"].set_text(f"chosen cats: {new_selection}")
        # CAT CONNECTIONS
        if self.connections_element.get("cat_list"):
            new_selection = (self.connections_element["cat_list"].selected_list.copy()
                             if self.connections_element["cat_list"].selected_list else [])
            if self.new_cat_info[self.open_connection] != new_selection:
                self.new_cat_info[self.open_connection] = new_selection
                self.connections_element["info"].set_text(f"chosen cats: {new_selection}")
        self.handle_main_and_random_cat_on_use()
        self.update_new_cat_tags()

    def handle_main_and_random_cat_on_use(self):
        # RANKS
        if (self.rank_element.get("dropdown")
                and self.rank_element["dropdown"].selected_list != self.current_cat_dict["rank"]):
            self.current_cat_dict["rank"] = self.rank_element["dropdown"].selected_list.copy()
            if self.current_cat_dict["rank"]:
                self.rank_element["info"].set_text(f"chosen rank: {self.current_cat_dict['rank']}")
            else:
                self.rank_element["info"].set_text(f"chosen rank: ['any']")
            self.editor_container.on_contained_elements_changed(self.rank_element["info"])
        # AGES
        if (self.age_element.get("dropdown")
                and self.age_element["dropdown"].selected_list != self.current_cat_dict["age"]):
            self.current_cat_dict["age"] = self.age_element["dropdown"].selected_list.copy()

            if self.current_cat_dict["age"]:
                self.age_element["info"].set_text(f"chosen age: {self.current_cat_dict['age']}")
            else:
                self.age_element["info"].set_text(f"chosen age: ['any']")
            self.editor_container.on_contained_elements_changed(self.age_element["info"])
        # SKILLS
        if self.skill_element.get("paths"):
            # chosen path has changed
            if (self.skill_element["paths"].selected_list
                    and self.open_path not in self.skill_element["paths"].selected_list):
                self.open_path = self.skill_element["paths"].selected_list[0]
                self.update_level_list()
            # there is no path selected
            elif not self.skill_element["paths"].selected_list and self.open_path:
                self.chosen_level = None
                self.update_skill_info()
                self.open_path = None
                self.update_level_list()
        # TRAITS
        if self.trait_element.get("adult"):
            combined_selection = self.trait_element["adult"].selected_list.copy()
            combined_selection.extend(self.trait_element["kitten"].selected_list)

            if not combined_selection:
                combined_selection = []

            saved_traits = "trait" if self.trait_allowed else "not_trait"
            if combined_selection != self.current_cat_dict[saved_traits]:
                self.update_trait_info(self.kit_traits, self.trait_element["kitten"].selected_list)
                self.update_trait_info(self.adult_traits, self.trait_element["adult"].selected_list)
        # BACKSTORIES
        if self.backstory_element.get("pools"):
            selected_list = self.backstory_element["pools"].selected_list

            if not self.open_pool and not selected_list:
                self.backstory_element["list"].new_item_list([])
                self.update_backstory_info()

            # pool has changed
            elif selected_list and self.open_pool not in selected_list:
                self.open_pool = selected_list[0]
                self.backstory_element["list"].new_item_list(self.all_backstories[self.open_pool])

                for name, button in self.backstory_element["list"].buttons.items():
                    button.set_tooltip(f"cat.backstories.{name}")
                self.update_backstory_info()

            # there is no pool selected
            elif not selected_list and self.open_pool:
                if self.open_pool in self.current_cat_dict["backstory"]:
                    self.current_cat_dict["backstory"].remove(self.open_pool)

                singles_to_remove = set(self.current_cat_dict["backstory"]).intersection(
                    set(self.all_backstories[self.open_pool]))
                if singles_to_remove:
                    for story in singles_to_remove:
                        self.current_cat_dict["backstory"].remove(story)

                self.open_pool = None
                self.backstory_element["list"].new_item_list([])
                self.update_backstory_info()

    def handle_settings_on_use(self):
        # CHANGE TYPE
        if (self.type_element.get("pick_type")
                and self.type_element["pick_type"].selected_list != self.type_info):
            new_type = self.type_element["pick_type"].selected_list[0]
            self.type_element["pick_type"].parent_button.set_text(new_type)
            self.type_info = [new_type]
            self.sub_info.clear()
            self.update_sub_info()
            self.update_sub_buttons(self.event_types.get(new_type))
            self.update_basic_checkboxes()
        # CHANGE SUBTYPES
        if (self.type_element.get("subtype_dropdown")
                and self.type_element["subtype_dropdown"].selected_list != self.sub_info):
            self.sub_info = self.type_element["subtype_dropdown"].selected_list.copy()
            self.update_sub_info()
        # CHANGE SEASONS
        if (self.season_element.get("season_dropdown")
                and self.season_element["season_dropdown"].selected_list != self.season_info):
            self.season_info = self.season_element["season_dropdown"].selected_list.copy()
            self.update_season_info()

    def change_new_cat_info_dict(self):
        if not self.new_cat_info_dict.get(self.selected_new_cat):
            self.new_cat_info_dict[self.selected_new_cat] = {
                "backstory": [],
                "parent": [],
                "adoptive": [],
                "mate": []
            }
        self.new_cat_info = self.new_cat_info_dict[self.selected_new_cat]
        self.current_cat_dict = self.new_cat_info

    def update_new_cat_options(self):
        # BOOLS
        for info in self.new_cat_bools:
            if info["tag"] in self.new_cat_list[self.selected_new_cat] and not info["setting"]:
                info["setting"] = True
                self.new_cat_checkbox[info["tag"]].check()
            elif info["tag"] not in self.new_cat_list[self.selected_new_cat] and info["setting"]:
                info["setting"] = False
                self.new_cat_checkbox[info["tag"]].uncheck()

        # AVAILABLE CATS
        self.connections_element["cat_list"].new_item_list(self.get_involved_cats(
            index_limit=int(self.selected_new_cat.strip("n_c:"))
        ))

        # EVERYTHING ELSE
        cat_type = []
        stories = []
        pool = []
        rank = []
        age = []
        gender = []
        parent = []
        adopt = []
        mate = []

        for tag in self.new_cat_list[self.selected_new_cat]:
            if tag in self.new_cat_types:
                cat_type = [tag]
            elif "backstory" in tag:
                stories = tag.replace("backstory:", "")
                stories = stories.split(",")
                if not isinstance(stories, list):
                    stories = [stories]
                if stories:
                    for pool_name in self.all_backstories:
                        if pool_name in stories:
                            pool = pool_name
                else:
                    pool = []
            elif "status" in tag:
                rank = [tag.replace("status:", "")]
            elif "age" in tag:
                age = [tag.replace("age:", "")]
            elif tag in self.new_cat_genders:
                gender = [tag]
            elif "parent" in tag:
                parent = tag.replace("parent:", "").split(",")
            elif "adoptive" in tag:
                adopt = tag.replace("adoptive:", "").split(",")
            elif "mate" in tag:
                mate = tag.replace("mate:", "").split(",")

        self.cat_story_element["list"].set_selected_list(cat_type)
        self.backstory_element["pools"].set_selected_list(pool)
        self.backstory_element["list"].set_selected_list(stories)
        self.new_status_element["list"].set_selected_list(rank)
        self.new_age_element["list"].set_selected_list(age)
        self.new_gender_element["list"].set_selected_list(gender)
        if self.open_connection == "parent":
            self.connections_element["cat_list"].set_selected_list(parent)
        elif self.open_connection == "adoptive":
            self.connections_element["cat_list"].set_selected_list(adopt)
        elif self.open_connection == "mate":
            self.connections_element["cat_list"].set_selected_list(mate)

    def update_new_cat_tags(self):
        if not self.selected_new_cat:
            return

        selected_cat_info = self.new_cat_list[self.selected_new_cat]

        # BOOL TAGS
        for bool in self.new_cat_bools:
            if bool["setting"] and bool["tag"] not in selected_cat_info:
                selected_cat_info.append(bool["tag"])
            elif not bool["setting"] and bool["tag"] in selected_cat_info:
                selected_cat_info.remove(bool["tag"])

        # CAT TYPES
        selected_type = (self.cat_story_element["list"].selected_list[0]
                         if self.cat_story_element["list"].selected_list
                         else None)

        for cat_type in self.new_cat_types:
            if cat_type == selected_type and cat_type not in selected_cat_info:
                selected_cat_info.append(selected_type)
            if cat_type != selected_type and cat_type in selected_cat_info:
                selected_cat_info.remove(cat_type)

        # BACKSTORIES
        possible_stories = (list(self.all_backstories.keys()) + self.individual_stories)
        chosen_stories = set(possible_stories).intersection(self.new_cat_info["backstory"])

        new_story_tag = None
        if chosen_stories:
            new_story_tag = f"backstory:{','.join(chosen_stories)}"

        existing_tag = False
        for tag in selected_cat_info.copy():
            if "backstory" in tag and tag != new_story_tag:
                existing_tag = True
                selected_cat_info.remove(tag)
                break
            elif tag == new_story_tag:
                existing_tag = True
                break
            existing_tag = False

        if new_story_tag and not existing_tag:
            selected_cat_info.append(new_story_tag)

        # RANK
        if self.new_status_element['list'].selected_list:
            rank = self.new_status_element['list'].selected_list[0]
        else:
            rank = None

        new_rank_tag = f"status:{rank}" if rank else None

        existing_tag = False
        for tag in selected_cat_info.copy():
            if "status" in tag and tag != new_rank_tag:
                existing_tag = True
                selected_cat_info.remove(tag)
                break
            elif tag == new_rank_tag:
                existing_tag = True
                break
            existing_tag = False

        if new_rank_tag and not existing_tag:
            selected_cat_info.append(new_rank_tag)

        # AGE
        if self.new_age_element['list'].selected_list:
            age = self.new_age_element['list'].selected_list[0]
        else:
            age = None

        new_age_tag = f"age:{age}" if age else None

        existing_tag = False
        for tag in selected_cat_info.copy():
            if "age" in tag and tag != new_age_tag:
                existing_tag = True
                selected_cat_info.remove(tag)
                break
            elif tag == new_age_tag:
                existing_tag = True
                break
            existing_tag = False

        if new_age_tag and not existing_tag:
            selected_cat_info.append(new_age_tag)

        # GENDER
        if self.new_gender_element['list'].selected_list:
            gender = self.new_gender_element['list'].selected_list[0]
        else:
            gender = None

        if gender and gender not in selected_cat_info:
            for option in self.new_cat_genders:
                if option in selected_cat_info:
                    selected_cat_info.remove(option)
            selected_cat_info.append(gender)

        elif not gender:
            for option in self.new_cat_genders:
                if option in selected_cat_info:
                    selected_cat_info.remove(option)

        # CAT CONNECTIONS
        if self.connections_element["cat_list"].selected_list:
            connections = self.connections_element["cat_list"].selected_list
        else:
            connections = []

        new_tag = None
        if connections:
            new_tag = f"{self.open_connection}:{','.join(connections)}"

        if new_tag and new_tag not in selected_cat_info:
            for tag in selected_cat_info.copy():
                if self.open_connection in tag:
                    selected_cat_info.remove(tag)
                    break
            selected_cat_info.append(new_tag)

        elif not new_tag:
            for tag in selected_cat_info.copy():
                if self.open_connection in tag:
                    selected_cat_info.remove(tag)

        if self.new_cat_editor["info"].html_text != f"selected cat: {selected_cat_info}":
            self.new_cat_editor["info"].set_text(f"selected cat: {selected_cat_info}")

        self.editor_container.on_contained_elements_changed(self.new_cat_editor["info"])

    # MAIN/RANDOM CAT UPDATES
    def update_backstory_info(self):
        chosen_stories = self.current_cat_dict["backstory"]

        if self.open_pool:
            pool = self.all_backstories[self.open_pool]

            # pool category added only if none of its stories have been selected
            if self.open_pool not in chosen_stories and not set(chosen_stories).intersection(set(pool)):
                chosen_stories.append(self.open_pool)

        self.backstory_element["info"].set_text(f"chosen backstory: {chosen_stories}")
        self.editor_container.on_contained_elements_changed(self.backstory_element["info"])

    def update_trait_info(self, trait_dict, selected_list):
        saved_traits = "trait" if self.trait_allowed else "not_trait"

        selected_traits = set(self.current_cat_dict[saved_traits]).intersection(trait_dict)
        if selected_list != selected_traits:
            removed = [trait for trait in selected_traits
                       if trait not in selected_list]
            added = [trait for trait in selected_list
                     if trait not in selected_traits]
            if removed:
                for trait in removed:
                    self.current_cat_dict[saved_traits].remove(trait)
            if added:
                self.current_cat_dict[saved_traits].extend(added)

        if self.trait_allowed:
            self.trait_element["include_info"].set_text(f"chosen allowed traits: {self.current_cat_dict['trait']}")
            self.editor_container.on_contained_elements_changed(self.trait_element["include_info"])
        else:
            self.trait_element["exclude_info"].set_text(f"chosen excluded traits: {self.current_cat_dict['not_trait']}")
            self.editor_container.on_contained_elements_changed(self.trait_element["exclude_info"])

    def update_skill_info(self):

        skill_tag = f"{self.open_path},{self.chosen_level if self.chosen_level else 0}"

        if self.skill_allowed:
            already_tagged = [tag for tag in self.current_cat_dict["skill"] if self.open_path in tag]
            if already_tagged:
                self.current_cat_dict["skill"].remove(already_tagged[0])
            if self.chosen_level:
                self.current_cat_dict["skill"].append(skill_tag)
            self.skill_element["include_info"].set_text(f"chosen allowed skills: {self.current_cat_dict['skill']}")
            self.editor_container.on_contained_elements_changed(self.skill_element["include_info"])
        else:
            already_tagged = [tag for tag in self.current_cat_dict["not_skill"] if self.open_path in tag]
            if already_tagged:
                self.current_cat_dict["not_skill"].remove(already_tagged[0])
            if self.chosen_level:
                self.current_cat_dict["not_skill"].append(skill_tag)
            self.skill_element["exclude_info"].set_text(f"chosen excluded skills: {self.current_cat_dict['not_skill']}")
            self.editor_container.on_contained_elements_changed(self.skill_element["exclude_info"])

    def update_rel_status_info(self):

        for info in self.rel_tag_list:
            if info["tag"] not in self.current_cat_dict['rel_status'] and info["setting"]:
                self.current_cat_dict["rel_status"].append(info["tag"])
            elif info["tag"] in self.current_cat_dict['rel_status'] and not info["setting"]:
                self.current_cat_dict["rel_status"].remove(info["tag"])

        if self.rel_status_element.get("info"):
            self.rel_status_element["info"].set_text(
                f"chosen relationship_status: {self.current_cat_dict['rel_status']}")
            self.editor_container.on_contained_elements_changed(self.rel_status_element["info"])

    # SETTINGS UPDATES
    def replace_accs_with_group(self, group):
        for category_name, accs in self.acc_categories.items():
            if group == category_name:
                for acc in set(self.acc_info).intersection(set(accs)):
                    self.acc_info.remove(acc)
                break

        if group not in self.acc_info:
            self.acc_info.append(group)

    def update_acc_info(self):

        if self.acc_info:
            for category_name, accs, in self.acc_categories.items():
                if category_name in self.acc_info and set(self.acc_info).intersection(set(accs)):
                    self.acc_info.remove(category_name)
                    break
            self.acc_element["acc_info"].set_text(f"chosen accessories: {self.acc_info}")
        else:
            self.acc_element["acc_info"].set_text(f"chosen accessories: []")

        self.editor_container.on_contained_elements_changed(self.acc_element["acc_info"])

    def update_tag_info(self):

        for info in self.basic_tag_list:
            if info["tag"] not in self.tag_info and info["setting"]:
                self.tag_info.append(info["tag"])
            elif info["tag"] in self.tag_info and not info["setting"]:
                self.tag_info.remove(info["tag"])

        for rank, box in self.rank_tag_checkbox.items():
            if "_text" in rank:
                continue
            tag = f"clan:{rank}".replace(" ", "_")
            if box.checked and tag not in self.tag_info:
                self.tag_info.append(tag)
            elif not box.checked and tag in self.tag_info:
                self.tag_info.remove(tag)

        if self.tag_element.get("tag_display"):
            self.tag_element["tag_display"].set_text(f"chosen tags: {self.tag_info}")
            self.editor_container.on_contained_elements_changed(self.tag_element["tag_display"])

    def update_location_info(self, biome=None, camp=None):

        if biome:
            biome = biome.casefold()
            present = False
            for location in self.location_info:
                if biome in location:
                    present = True
                    break
            if not present:
                self.location_info.append(biome)
                self.update_camp_list(biome.capitalize())

            else:
                for location in self.location_info:
                    if biome in location:
                        self.location_info.remove(location)
                        self.update_camp_list(None)
                        break

        if camp:
            present = True
            parent_biome = None
            camp_index = 0
            old_location_tag = None
            new_string = None

            for camp_biome in self.all_camps.keys():
                if camp in self.all_camps[camp_biome]:
                    parent_biome = camp_biome
                    camp_index = self.all_camps[camp_biome].index(camp) + 1
                    break

            for location in self.location_info:
                if parent_biome.casefold() in location:
                    if f"camp{camp_index}" in location:
                        break
                    else:
                        new_string = f"{location}_camp{camp_index}"
                        present = False
                        old_location_tag = location
                        break
            if not present:
                self.location_info.remove(old_location_tag)
                self.location_info.append(new_string.casefold())
            else:
                for location in self.location_info:
                    if parent_biome.casefold() in location:
                        old_location_tag = location
                        new_string = location.replace(f"_camp{camp_index}", "")
                        break
                self.location_info.remove(old_location_tag)
                self.location_info.append(new_string)

        self.location_element["location_display"].set_text((f"chosen location: {str(self.location_info)}"
                                                            if self.location_info
                                                            else "chosen location: ['any']"))
        self.editor_container.on_contained_elements_changed(self.location_element["location_display"])

    def update_season_info(self):

        if self.season_info:
            self.season_element["season_display"].set_text(f"chosen season: {self.season_info}")
        else:
            self.season_element["season_display"].set_text("chosen season: ['any']")

    def update_sub_info(self):
        if "accessory" not in self.sub_info:
            for group in self.acc_categories.keys():
                self.acc_element[group].disable()
                if self.acc_element.get("acc_display"):
                    self.acc_element["acc_display"].kill()
                self.acc_info.clear()
                self.update_acc_info()

        if self.sub_info:
            if "accessory" in self.sub_info:
                for group in self.acc_categories.keys():
                    self.acc_element[group].enable()

            self.type_element["sub_display"].set_text(f"chosen subtypes: {self.sub_info}")
        else:
            self.type_element["sub_display"].set_text("chosen subtypes: []")

    # OVERALL SCREEN CONTROLS
    def exit_screen(self):
        self.chosen_biome = None
        self.chosen_type = None
        self.chosen_event = None
        self.location_info = []
        self.season_info = []
        self.type_info = []
        self.sub_info = []
        self.tag_info = []

        self.main_menu_button.kill()
        self.list_frame.kill()
        self.event_text_container.kill()
        if self.event_list_container:
            self.event_list_container.kill()
        if self.editor_container:
            self.editor_container.kill()
        if self.editor_element:
            for ele in self.editor_element.values():
                ele.kill()

        self.add_button.kill()
        self.kill_tabs()
        self.kill_event_buttons()

    def clear_editor_tab(self):

        self.editor_container.kill()

        self.display_editor()

    def screen_switches(self):

        super().screen_switches()
        Screens.show_mute_buttons()

        self.main_menu_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (152, 30))),
            "buttons.main_menu",
            get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_squoval",
            starting_height=1,
        )

        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((60, 80), (250, 560))),
            get_box(BoxStyles.ROUNDED_BOX, (250, 560)),
            starting_height=3,
            manager=MANAGER,
        )

        self.select_type_tab_creation()

        self.event_text_container = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((290, 30), (0, 0))),
            starting_height=1,
            manager=MANAGER,
        )
        self.event_text_element["preview_button"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((-30, 10), (36, 36))),
            Icon.MAGNIFY,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            container=self.event_text_container,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.preview_text"
        )

        self.event_text_element["box"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 0), (460, 120))),
            get_box(BoxStyles.ROUNDED_BOX, (460, 120)),
            starting_height=1,
            manager=MANAGER,
            container=self.event_text_container
        )
        self.event_text_element["box"].disable()

        self.editor_element["frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((300, 140), (470, 490))),
            get_box(BoxStyles.FRAME, (470, 490)),
            starting_height=2,
            manager=MANAGER,
        )
        self.add_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 580), (36, 36))),
            Icon.NOTEPAD,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.add_event"
        )

        self.editor_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((314, 150), (470, 470))),
            starting_height=4,
            manager=MANAGER,
            allow_scroll_y=True,
        )
        self.editor_container.scrollable_container.resize_top = False

        self.editor_element["intro_text"] = UITextBoxTweaked(
            "screens.event_edit.intro_text",
            ui_scale(pygame.Rect((0, 0), (450, -1))),
            object_id="#text_box_26_horizleft_pad_10_14",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        if not self.current_editor_tab:
            self.current_editor_tab = "new cats"

    # EVENT DISPLAY
    def kill_tabs(self):
        for tab in self.type_tab_buttons:
            self.type_tab_buttons[tab].kill()
        for tab in self.biome_tab_buttons:
            self.biome_tab_buttons[tab].kill()

    def select_type_tab_creation(self):
        # clear all tabs first
        self.kill_tabs()
        # TODO: replace with a for loop
        self.type_tab_buttons["death"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 136), (36, 36))),
            Icon.STARCLAN,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_deaths"
        )
        self.type_tab_buttons["injury"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.SCRATCHES,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_injuries",
            anchors={
                "top_target": self.type_tab_buttons["death"]
            }
        )
        self.type_tab_buttons["misc"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.CLAN_UNKNOWN,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_misc",
            anchors={
                "top_target": self.type_tab_buttons["injury"]
            }
        )
        self.type_tab_buttons["new_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.CAT_HEAD,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_new_cat",
            anchors={
                "top_target": self.type_tab_buttons["misc"]
            }
        )

    def select_biome_tab_creation(self):
        # clear all tabs first
        self.kill_tabs()

        self.biome_tab_buttons["back"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 90), (36, 36))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1
        )
        self.biome_tab_buttons["general"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.PAW,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_general",
            anchors={
                "top_target": self.biome_tab_buttons["back"]
            }
        )
        self.biome_tab_buttons["forest"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.LEAFFALL,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_forest",
            anchors={
                "top_target": self.biome_tab_buttons["general"]
            }
        )
        self.biome_tab_buttons["mountainous"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.LEAFBARE,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_mountain",
            anchors={
                "top_target": self.biome_tab_buttons["forest"]
            }
        )
        self.biome_tab_buttons["plains"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.NEWLEAF,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_plains",
            anchors={
                "top_target": self.biome_tab_buttons["mountainous"]
            }
        )
        self.biome_tab_buttons["beach"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.DARKFOREST,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_beach",
            anchors={
                "top_target": self.biome_tab_buttons["plains"]
            }
        )

        self.biome_tab_buttons["desert"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.GREENLEAF,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_desert",
            anchors={
                "top_target": self.biome_tab_buttons["beach"]
            }
        )

        self.biome_tab_buttons["wetlands"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.HERB,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_wetlands",
            anchors={
                "top_target": self.biome_tab_buttons["desert"]
            }
        )

    def display_events(self):
        self.kill_event_buttons()
        self.event_list = None
        if self.editor_element.get("intro_text"):
            self.editor_element["intro_text"].set_text("screens.event_edit.intro_text")

        path = f"resources/lang/en/events/{self.chosen_type}/{self.chosen_biome.casefold()}.json"

        try:
            with open(path, "r", encoding="utf-8") as read_file:
                events = read_file.read()
                self.event_list = ujson.loads(events)
        except:
            print(f"Something went wrong with event loading. Is {path} valid?")

        if not self.event_list:
            self.editor_element["intro_text"].set_text("screens.event_edit.empty_event_list")
            return

        try:
            if not isinstance(self.event_list[0], dict):
                print(f"{path} isn't in the correct event format. Perhaps it isn't an event .json?")
        except KeyError:
            return

        self.event_list_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((70, 90), (230, 540))),
            starting_height=3,
            manager=MANAGER,
            allow_scroll_y=True,
        )

        x = 0
        for event in self.event_list:
            self.event_buttons[x] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 0), (230, 36))),
                event["event_id"],
                get_button_dict(ButtonStyles.DROPDOWN, (230, 36)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                starting_height=1,
                anchors={
                    "top_target": self.event_buttons[x - 1]
                } if self.event_buttons.get(x - 1) else None,
                container=self.event_list_container,
                tool_tip_text=event["event_text"]
            )
            x += 1

    def kill_event_buttons(self):
        for event in self.event_buttons:
            self.event_buttons[event].kill()

    # EDITOR DISPLAY
    def display_editor(self):

        self.editor_element["intro_text"].kill()

        # EVENT TEXT
        # this one is special in that it has a separate container
        if not self.event_text_element.get("preview_text"):
            self.event_text_element["preview_text"] = UITextBoxTweaked(
                "",
                ui_scale(pygame.Rect((48, 10), (435, 100))),
                object_id="#text_box_26_horizleft_pad_10_14",
                manager=MANAGER,
                container=self.event_text_container,
                visible=False,
            )
            self.event_text_element["preview_text"].disable()
            self.event_text_element["event_text"] = pygame_gui.elements.UITextEntryBox(
                ui_scale(pygame.Rect((48, 10), (435, 100))),
                placeholder_text="screens.event_edit.event_text_initial",
                object_id="#text_box_26_horizleft_pad_10_14",
                manager=MANAGER,
                container=self.event_text_container,
            )

        # SECTION TABS
        if not self.editor_element.get(list(self.section_tabs.keys())[0]):
            prev_element = None
            for name, icon in self.section_tabs.items():
                self.editor_element[name] = UISurfaceImageButton(
                    ui_scale(pygame.Rect((10, -6), (36, 36))),
                    icon,
                    get_button_dict(ButtonStyles.ICON_TAB_BOTTOM, (36, 36)),
                    manager=MANAGER,
                    object_id="@buttonstyles_icon_tab_bottom",
                    starting_height=1,
                    tool_tip_text=name,
                    anchors=(
                        {
                            "top_target": self.editor_element["frame"],
                            "left_target": self.list_frame
                        }
                        if not prev_element
                        else
                        {
                            "top_target": self.editor_element["frame"],
                            "left_target": prev_element
                        }
                    )
                )
                prev_element = self.editor_element[name]

        if self.current_editor_tab == "settings":
            self.generate_settings_tab()
        elif self.current_editor_tab == "main cat":
            self.current_cat_dict = self.main_cat_info
            self.generate_main_cat_tab()
        elif self.current_editor_tab == "random cat":
            self.current_cat_dict = self.random_cat_info
            self.generate_random_cat_tab()
        elif self.current_editor_tab == "new cats":
            self.current_cat_dict = self.new_cat_info
            self.generate_new_cats_tab()

    def create_divider(self, top_anchor, name, off_set: int = -12):

        self.editor_element[name] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, off_set), (524, 24))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/spacer.png"
                ).convert_alpha(),
                ui_scale_dimensions((524, 24)),
            ),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": top_anchor
            }
        )

    # NEW CATS EDITOR
    def generate_new_cats_tab(self):
        self.new_cat_editor["intro"] = UITextBoxTweaked(
            "screens.event_edit.n_c_info",
            ui_scale(pygame.Rect((0, 10), (295, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        self.new_cat_editor["frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((12, 20), (112, 186))),
            get_box(BoxStyles.FRAME, (112, 186)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "left_target": self.new_cat_editor["intro"]
            }
        )

        # TODO: consider tooltips to show the hovered cat's tag info
        self.new_cat_editor["cat_list"] = UIScrollingButtonList(
            pygame.Rect((20, 28), (100, 168)),
            item_list=self.new_cat_list.keys(),
            button_dimensions=(96, 30),
            multiple_choice=False,
            disable_selection=True,
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "left_target": self.new_cat_editor["intro"]
            }
        )

        self.new_cat_editor["add"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((30, 4), (36, 36))),
            "+",
            get_button_dict(ButtonStyles.ICON_TAB_BOTTOM, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_bottom",
            container=self.editor_container,
            anchors={
                "top_target": self.new_cat_editor["cat_list"],
                "left_target": self.new_cat_editor["intro"]
            },
            tool_tip_text="add a new cat"
        )

        self.new_cat_editor["delete"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((5, 4), (36, 36))),
            "-",
            get_button_dict(ButtonStyles.ICON_TAB_BOTTOM, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_bottom",
            container=self.editor_container,
            anchors={
                "top_target": self.new_cat_editor["cat_list"],
                "left_target": self.new_cat_editor["add"]
            },
            tool_tip_text="delete selected cat"
        )

        self.new_cat_editor["info"] = UITextBoxTweaked(
            "No cat selected",
            ui_scale(pygame.Rect((0, 0), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.new_cat_editor["intro"]
            }
        )

        self.create_divider(self.new_cat_editor["info"], "info")

    def clear_new_cat_constraints(self):
        for ele in self.new_cat_checkbox.values():
            ele.kill()
        self.new_cat_checkbox.clear()
        for ele in self.new_cat_element.values():
            ele.kill()
        self.new_cat_element.clear()

    def display_new_cat_constraints(self):

        self.clear_new_cat_constraints()

        # BOOLS
        self.create_bool_editor()

        # BACKSTORY
        self.create_story_editor()

        # STATUS
        self.create_new_cat_status_editor()

        # AGE
        self.create_new_cat_age_editor()

        # GENDER
        self.create_new_cat_gender_editor()

        # PARENT/ADOPTIVE/MATE
        self.connections_element["birth_parent"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((50, 20), (120, 30))),
            "birth parents",
            get_button_dict(ButtonStyles.MENU_LEFT, (120, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_left",
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["gender"],
            }
        )
        # parent is picked by default, so this is initially disabled
        self.connections_element["birth_parent"].disable()

        self.connections_element["adopt_parent"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 20), (140, 30))),
            "adoptive parents",
            get_button_dict(ButtonStyles.MENU_MIDDLE, (140, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_middle",
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["gender"],
                "left_target": self.connections_element["birth_parent"]
            }
        )
        self.connections_element["mate"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 20), (80, 30))),
            "mates",
            get_button_dict(ButtonStyles.MENU_RIGHT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_right",
            container=self.editor_container,
            anchors={
                "left_target": self.connections_element["adopt_parent"],
                "top_target": self.editor_element["gender"]
            }
        )

        self.connections_element["text"] = UITextBoxTweaked(
            "screens.event_edit.new_cat_parent_info",
            ui_scale(pygame.Rect((0, 14), (260, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.connections_element["adopt_parent"]
            }
        )
        self.connections_element["info"] = UITextBoxTweaked(
            "chosen cats: []",
            ui_scale(pygame.Rect((0, 10), (260, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.connections_element["text"]
            }
        )
        self.connections_element["frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((12, 20), (132, 166))),
            get_box(BoxStyles.FRAME, (132, 166)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.connections_element["mate"],
                "left_target": self.connections_element["text"]
            }
        )

        self.connections_element["cat_list"] = UIScrollingButtonList(
            pygame.Rect((20, 28), (120, 148)),
            item_list=self.get_involved_cats(index_limit=int(self.selected_new_cat.strip("n_c:"))),
            button_dimensions=(116, 30),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": self.connections_element["mate"],
                "left_target": self.connections_element["text"]
            }
        )
        self.create_divider(self.connections_element["frame"], "connections")

    def get_involved_cats(self, index_limit=None):
        """
        :param index_limit: indicate a maximum index for the new cat list.
        """
        # TODO: make sure this gets an option to indicate if r_c is in the event
        involved_cats = ["m_c"]
        if self.random_cat_info:
            involved_cats.append("r_c")

        new_cat_list = list(self.new_cat_list.keys())
        if isinstance(index_limit, int):
            for index, item in enumerate(new_cat_list.copy()):
                if index >= index_limit:
                    new_cat_list.remove(item)

        involved_cats.extend(new_cat_list)

        return involved_cats

    def create_new_cat_gender_editor(self):
        self.new_gender_element["text"] = UITextBoxTweaked(
            "screens.event_edit.new_cat_gender_info",
            ui_scale(pygame.Rect((0, 14), (290, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["age"]
            }
        )
        self.new_gender_element["list"] = UIDropDown(
            ui_scale(pygame.Rect((0, 26), (130, 30))),
            parent_text="options",
            item_list=self.new_cat_genders,
            disable_selection=False,
            container=self.editor_container,
            child_trigger_close=True,
            parent_reflect_selection=True,
            anchors={
                "top_target": self.editor_element["age"],
                "left_target": self.new_gender_element["text"]
            },
            manager=MANAGER
        )
        self.create_divider(self.new_gender_element["text"], "gender")

    def create_new_cat_age_editor(self):
        self.new_age_element["text"] = UITextBoxTweaked(
            "screens.event_edit.new_cat_age_info",
            ui_scale(pygame.Rect((0, 14), (290, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["rank"]
            }
        )
        self.new_age_element["list"] = UIDropDown(
            ui_scale(pygame.Rect((0, 26), (130, 30))),
            parent_text="ages",
            item_list=self.new_cat_ages,
            disable_selection=False,
            container=self.editor_container,
            child_trigger_close=True,
            parent_reflect_selection=True,
            anchors={
                "top_target": self.editor_element["rank"],
                "left_target": self.new_age_element["text"]
            },
            manager=MANAGER
        )
        self.new_age_element["list"].child_button_dicts["mate"].set_tooltip("screens.event_edit.mate")
        self.new_age_element["list"].child_button_dicts["has_kits"].set_tooltip("screens.event_edit.has_kits")
        self.create_divider(self.new_age_element["text"], "age")

    def create_new_cat_status_editor(self):
        self.new_status_element["text"] = UITextBoxTweaked(
            "screens.event_edit.new_cat_rank_info",
            ui_scale(pygame.Rect((0, 14), (260, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["backstory"]
            }
        )
        self.new_status_element["list"] = UIDropDown(
            ui_scale(pygame.Rect((0, 26), (180, 30))),
            parent_text="ranks",
            item_list=self.new_cat_ranks,
            disable_selection=False,
            container=self.editor_container,
            child_trigger_close=True,
            parent_reflect_selection=True,
            anchors={
                "top_target": self.editor_element["backstory"],
                "left_target": self.new_status_element["text"]
            },
            manager=MANAGER
        )
        self.create_divider(self.new_status_element["text"], "rank")

    def create_story_editor(self):
        self.cat_story_element["text"] = UITextBoxTweaked(
            "screens.event_edit.cat_type_info",
            ui_scale(pygame.Rect((0, 14), (310, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["bools"]
            }
        )
        self.cat_story_element["list"] = UIDropDown(
            ui_scale(pygame.Rect((10, 26), (100, 30))),
            parent_text="types",
            item_list=self.new_cat_types,
            disable_selection=False,
            container=self.editor_container,
            child_trigger_close=True,
            parent_reflect_selection=True,
            anchors={
                "top_target": self.editor_element["bools"],
                "left_target": self.cat_story_element["text"]
            },
            manager=MANAGER
        )
        self.create_backstory_editor(self.cat_story_element["text"])
        self.create_divider(self.backstory_element["info"], "backstory")

    def create_bool_editor(self):
        self.new_cat_element["checkbox_container"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((20, 0), (0, 0))),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": self.editor_element["info"]
            }
        )
        prev_element = None
        for info in self.new_cat_bools:
            self.new_cat_checkbox[info["tag"]] = UICheckbox(
                position=(0, 15),
                container=self.new_cat_element["checkbox_container"],
                manager=MANAGER,
                check=info["setting"],
                anchors={
                    "top_target": prev_element
                } if prev_element else None
            )

            self.new_cat_checkbox[f"{info['tag']}_text"] = UITextBoxTweaked(
                f"screens.event_edit.{info['tag']}",
                ui_scale(pygame.Rect((50, 10), (370, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.new_cat_element["checkbox_container"],
                anchors={
                    "top_target": prev_element,
                } if prev_element else None
            )

            prev_element = self.new_cat_checkbox[f"{info['tag']}_text"]

        self.create_divider(prev_element, "bools")

    # MAIN/RANDOM CAT EDITOR
    def generate_main_cat_tab(self):
        self.main_cat_editor["intro"] = UITextBoxTweaked(
            "screens.event_edit.mass_death_info" if "mass_death" in self.sub_info else "screens.event_edit.m_c_info",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        # DEATH
        self.create_dies_editor(self.main_cat_editor)

        # RANK
        self.create_rank_editor()

        # AGE
        self.create_age_editor()

        # REL STATUS
        self.create_rel_status_editor()

        # SKILLS
        self.create_skill_editor()

        # TRAITS
        self.create_trait_editor()

        # BACKSTORIES
        self.create_backstory_editor()

    def generate_random_cat_tab(self):
        self.random_cat_editor["intro"] = UITextBoxTweaked(
            "screens.event_edit.r_c_info",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        # DEATH
        self.create_dies_editor(self.random_cat_editor)

        # RANK
        self.create_rank_editor()

        # AGE
        self.create_age_editor()

        # REL STATUS
        self.create_rel_status_editor()

        # SKILLS
        self.create_skill_editor()

        # TRAITS
        self.create_trait_editor()

        # BACKSTORIES
        self.create_backstory_editor()

    def create_backstory_editor(self, prev_element=None):
        prev_element = prev_element if prev_element else self.editor_element["traits"]

        self.backstory_element["text"] = UITextBoxTweaked(
            "screens.event_edit.backstory_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": prev_element
            }
        )
        self.backstory_element["pools"] = UIScrollingButtonList(
            pygame.Rect((25, 20), (200, 198)),
            item_list=[pool for pool in self.all_backstories.keys()],
            button_dimensions=(200, 30),
            multiple_choice=False,
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["text"]
            },
            manager=MANAGER
        )
        self.backstory_element["frame"] = UIModifiedImage(
            ui_scale(pygame.Rect((-20, 30), (180, 170))),
            get_box(BoxStyles.ROUNDED_BOX, (180, 170)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["text"],
                "left_target": self.backstory_element["pools"]
            }
        )
        self.backstory_element["frame"].disable()
        self.backstory_element["list"] = UIScrollingButtonList(
            pygame.Rect((-4, 38), (156, 152)),
            item_list=[],
            button_dimensions=(156, 30),
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["text"],
                "left_target": self.backstory_element["pools"]
            },
            manager=MANAGER
        )
        self.backstory_element["info"] = UITextBoxTweaked(
            "chosen backstories: []",
            ui_scale(pygame.Rect((10, 20), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.backstory_element["pools"],
            },
            allow_split_dashes=False
        )
        self.create_divider(self.backstory_element["info"], "backstory")

    def create_trait_editor(self):
        self.trait_element["text"] = UITextBoxTweaked(
            "screens.event_edit.trait_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["skills"]
            }
        )
        self.trait_element["allow"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((130, 10), (80, 30))),
            "allow",
            get_button_dict(ButtonStyles.MENU_LEFT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_left",
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["text"]
            }
        )
        # allow is picked by default, so this is initially disabled
        self.trait_element["allow"].disable()
        self.trait_element["exclude"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 10), (80, 30))),
            "exclude",
            get_button_dict(ButtonStyles.MENU_RIGHT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_right",
            container=self.editor_container,
            anchors={
                "left_target": self.trait_element["allow"],
                "top_target": self.trait_element["text"]
            }
        )
        self.trait_element["kitten"] = UIScrollingDropDown(
            pygame.Rect((30, 20), (140, 30)),
            dropdown_dimensions=(140, 198),
            item_list=self.kit_traits,
            parent_text="kitten traits",
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["allow"]
            },
            manager=MANAGER
        )
        self.trait_element["adult"] = UIScrollingDropDown(
            pygame.Rect((110, 20), (140, 30)),
            dropdown_dimensions=(140, 198),
            item_list=self.adult_traits,
            parent_text="adult traits",
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["allow"],
            },
            manager=MANAGER
        )
        self.trait_element["include_info"] = UITextBoxTweaked(
            "chosen allowed traits: []",
            ui_scale(pygame.Rect((10, 50), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["allow"],
            },
            allow_split_dashes=False
        )
        self.trait_element["exclude_info"] = UITextBoxTweaked(
            "chosen excluded traits: []",
            ui_scale(pygame.Rect((10, 0), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.trait_element["include_info"],
            },
            allow_split_dashes=False
        )
        self.create_divider(self.trait_element["exclude_info"], "traits")

    def create_skill_editor(self):
        self.skill_element["text"] = UITextBoxTweaked(
            "screens.event_edit.skill_info",
            ui_scale(pygame.Rect((0, 14), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["rel_status"]
            }
        )
        self.skill_element["paths"] = UIScrollingButtonList(
            pygame.Rect((30, 20), (140, 198)),
            item_list=[path for path in self.all_skills.keys()],
            button_dimensions=(140, 30),
            multiple_choice=False,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["text"]
            },
            manager=MANAGER
        )
        self.skill_element["allow"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((30, 20), (80, 30))),
            "allow",
            get_button_dict(ButtonStyles.MENU_LEFT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_left",
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["text"],
                "left_target": self.skill_element["paths"]
            }
        )
        # allow is picked by default, so this is initially disabled
        self.skill_element["allow"].disable()
        self.skill_element["exclude"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 20), (80, 30))),
            "exclude",
            get_button_dict(ButtonStyles.MENU_RIGHT, (80, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_menu_right",
            container=self.editor_container,
            anchors={
                "left_target": self.skill_element["allow"],
                "top_target": self.skill_element["text"]
            }
        )
        self.skill_element["frame"] = UIModifiedImage(
            ui_scale(pygame.Rect((-20, 20), (254, 130))),
            get_box(BoxStyles.ROUNDED_BOX, (254, 130)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["allow"],
                "left_target": self.skill_element["paths"]
            }
        )
        self.skill_element["frame"].disable()
        self.skill_element["include_info"] = UITextBoxTweaked(
            "chosen allowed skills: []",
            ui_scale(pygame.Rect((10, 20), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["paths"],
            },
            allow_split_dashes=False
        )
        self.skill_element["exclude_info"] = UITextBoxTweaked(
            "chosen excluded skills: []",
            ui_scale(pygame.Rect((10, 0), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.skill_element["include_info"],
            },
            allow_split_dashes=False
        )
        self.create_divider(self.skill_element["exclude_info"], "skills")

    def update_level_list(self):
        # kill existing buttons
        if self.level_element:
            for ele in self.level_element.values():
                ele.kill()

        # if no path is selected, don't make new buttons
        if not self.open_path:
            return

        # make new buttons
        level_list = (self.all_skills[self.open_path])
        prev_element = None
        for level in range(len(level_list)):
            self.level_element[f"{level + 1}"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((-4, (28 if not prev_element else -2)), (230, 30))),
                level_list[level],
                get_button_dict(ButtonStyles.DROPDOWN, (230, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "top_target": (self.skill_element["allow"]
                                   if not prev_element
                                   else prev_element),
                    "left_target": self.skill_element["paths"],
                }
            )
            prev_element = self.level_element[f"{level + 1}"]

    def create_dies_editor(self, editor):
        # TODO: set up a lock if subtype is death
        self.death_element["checkbox"] = UICheckbox(
            position=(7, 7),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": editor["intro"]
            },
            check=self.current_cat_dict["dies"]
        )
        self.death_element["text"] = UITextBoxTweaked(
            "screens.event_edit.death_info",
            ui_scale(pygame.Rect((40, 6), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": editor["intro"]
            }
        )
        self.death_element["info"] = UITextBoxTweaked(
            f"dies: {self.current_cat_dict['dies']}",
            ui_scale(pygame.Rect((0, 6), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.death_element["text"],
            }
        )
        self.create_divider(self.death_element["info"], "dies")

    def create_rel_status_editor(self):
        self.rel_status_element["container"] = UICollapsibleContainer(
            ui_scale(pygame.Rect((0, 0), (440, 0))),
            title_text="<b>relationship_status:</b>",
            top_button_oriented_left=False,
            bottom_button=False,
            scrolling_container_to_reset=self.editor_container,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["age"]
            }
        )
        self.rel_status_element["container"].close()
        # container for the checkbox list, this will get tossed into the collapsible container ^
        self.rel_status_element["checkboxes"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((48, 0), (0, 0))),
            container=self.rel_status_element["container"],
            manager=MANAGER,
            anchors={
                "top_target": self.rel_status_element["container"].top_button
            }
        )

        # only the main cat has access to these tags
        if self.current_editor_tab == "main cat":
            prev_element = None
            # CHECKBOXES
            # clear old elements
            if self.rel_status_checkbox:
                for info in self.rel_tag_list:
                    if self.rel_status_checkbox.get(f"{info['tag']}_text"):
                        self.rel_status_checkbox[f"{info['tag']}_text"].kill()
                    if self.rel_status_checkbox.get(info["tag"]):
                        self.rel_status_checkbox[info["tag"]].kill()
            # make new ones!
            for info in self.rel_tag_list:
                self.rel_status_element[f"{info['tag']}_text"] = UITextBoxTweaked(
                    f"screens.event_edit.{info['tag']}",
                    ui_scale(pygame.Rect((0, 10), (350, -1))),
                    object_id="#text_box_30_horizleft_pad_10_10",
                    line_spacing=1,
                    manager=MANAGER,
                    container=self.rel_status_element["checkboxes"],
                    anchors={
                        "top_target": prev_element,
                    } if prev_element else None
                )

                self.rel_status_checkbox[info["tag"]] = UICheckbox(
                    position=(350, 10),
                    container=self.rel_status_element["checkboxes"],
                    manager=MANAGER,
                    check=info["setting"],
                    anchors={
                        "top_target": prev_element
                    } if prev_element else None
                )

                prev_element = self.rel_status_element[f"{info['tag']}_text"]

        # VALUE TAGS
        self.rel_status_element["values"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((48, 0), (0, 0))),
            container=self.rel_status_element["container"],
            manager=MANAGER,
            anchors={
                "top_target": self.rel_status_element["checkboxes"]
            }
        )
        prev_element = None
        for value in self.rel_value_types:
            self.rel_status_element[f"{value}_text"] = UITextBoxTweaked(
                f"screens.event_edit.rel_values_{value}",
                ui_scale(pygame.Rect((0, 10), (-1, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.rel_status_element["values"],
                anchors={
                    "top_target": prev_element,
                } if prev_element else None
            )
            self.rel_value_element[f"{value}_entry"] = pygame_gui.elements.UITextEntryLine(
                ui_scale(pygame.Rect((250, 13), (40, 29))),
                manager=MANAGER,
                container=self.rel_status_element["values"],
                anchors={
                    "top_target": prev_element
                } if prev_element else None
            )
            self.rel_value_element[f"{value}_low_button"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((10, 12), (30, 30))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.DROPDOWN, (30, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.rel_status_element["values"],
                anchors=(
                    {
                        "left_target": self.rel_value_element[f"{value}_entry"],
                        "top_target": prev_element
                    }
                    if prev_element
                    else
                    {
                        "left_target": self.rel_value_element[f"{value}_entry"],
                    }
                )
            )
            self.rel_value_element[f"{value}_mid_button"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((-2, 12), (30, 30))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.DROPDOWN, (30, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.rel_status_element["values"],
                anchors=(
                    {
                        "left_target": self.rel_value_element[f"{value}_low_button"],
                        "top_target": prev_element
                    }
                    if prev_element
                    else
                    {
                        "left_target": self.rel_value_element[f"{value}_low_button"],
                    }
                )
            )
            self.rel_value_element[f"{value}_high_button"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((-2, 12), (30, 30))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.DROPDOWN, (30, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.rel_status_element["values"],
                anchors=(
                    {
                        "left_target": self.rel_value_element[f"{value}_mid_button"],
                        "top_target": prev_element
                    }
                    if prev_element
                    else
                    {
                        "left_target": self.rel_value_element[f"{value}_mid_button"],
                    }
                )
            )
            prev_element = self.rel_status_element[f"{value}_text"]
        self.rel_status_element["info"] = UITextBoxTweaked(
            f"chosen relationship_status: []",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.rel_status_element["container"]
            }
        )
        self.create_divider(self.rel_status_element["info"], "rel_status")

    def create_age_editor(self):
        self.age_element["text"] = UITextBoxTweaked(
            "screens.event_edit.age_info",
            ui_scale(pygame.Rect((0, 6), (220, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["rank"]
            }
        )
        self.age_element["dropdown"] = UIScrollingDropDown(
            pygame.Rect((0, 16), (200, 30)),
            manager=MANAGER,
            container=self.editor_container,
            parent_text="ages",
            item_list=self.all_ages,
            dropdown_dimensions=(200, 198),
            anchors={
                "top_target": self.editor_element["rank"],
                "left_target": self.age_element["text"]
            },
            starting_height=1
        )
        self.age_element["info"] = UITextBoxTweaked(
            f"chosen age: ['any']",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.age_element["text"]
            }
        )
        self.create_divider(self.age_element["info"], "age")

    def create_rank_editor(self):
        self.rank_element["text"] = UITextBoxTweaked(
            "screens.event_edit.rank_info",
            ui_scale(pygame.Rect((0, 10), (220, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.editor_element["dies"]
            }
        )
        self.rank_element["dropdown"] = UIScrollingDropDown(
            pygame.Rect((0, 28), (200, 30)),
            manager=MANAGER,
            container=self.editor_container,
            parent_text="ranks",
            item_list=self.all_ranks,
            dropdown_dimensions=(200, 310),
            starting_height=2,
            anchors={
                "top_target": self.death_element["info"],
                "left_target": self.rank_element["text"]
            }
        )
        self.rank_element["info"] = UITextBoxTweaked(
            f"chosen rank: ['any']",
            ui_scale(pygame.Rect((0, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.rank_element["text"]
            }
        )
        self.create_divider(self.rank_element["info"], "rank")

    # SETTINGS EDITOR
    def generate_settings_tab(self):
        # EVENT ID
        self.create_event_id_editor()
        # LOCATION
        self.create_location_editor()
        # SEASON
        self.create_season_editor()
        # TYPE AND SUBTYPES
        self.create_type_editor()
        # TAGS
        self.create_tag_editor()
        # WEIGHT
        self.create_weight_editor()
        # ACC
        self.create_acc_editor()

    def create_acc_editor(self):
        self.acc_element["acc_text"] = UITextBoxTweaked(
            "screens.event_edit.acc_info",
            ui_scale(pygame.Rect((0, 15), (450, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.weight_element["weight_text"]
            }
        )
        prev_element = None
        for group in self.acc_categories.keys():
            self.acc_element[group] = UISurfaceImageButton(
                ui_scale(pygame.Rect((40, 15), (150, 30))),
                group,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "top_target": (prev_element
                                   if prev_element
                                   else self.acc_element["acc_text"])
                }
            )
            prev_element = self.acc_element[group]
            self.acc_element[group].disable()

        self.acc_element["frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((-8, 0), (210, 250))),
            get_box(BoxStyles.FRAME, (210, 250)),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.acc_element["acc_text"],
                "left_target": prev_element
            }
        )

        self.acc_element["acc_info"] = UITextBoxTweaked(
            "chosen accessories: []",
            ui_scale(pygame.Rect((10, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.acc_element["frame"],
            },
            allow_split_dashes=False
        )

    def update_acc_list(self):
        # kill old buttons
        if self.acc_element.get("acc_display"):
            self.acc_element["acc_display"].kill()

        if not self.open_category:
            # if no category, we kill buttons and return
            return

        category = None
        for category_name, accs in self.acc_categories.items():
            if self.open_category == category_name:
                category = accs
                break

        self.acc_element["acc_display"] = UIScrollingButtonList(
            ui_scale(pygame.Rect((2, 10), (196, 230))),
            item_list=category,
            button_dimensions=(190, 30),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.acc_element["acc_text"],
                "left_target": self.acc_element["WILD"]
            },
        )

    def create_weight_editor(self):
        self.weight_element["weight_text"] = UITextBoxTweaked(
            "<b>* weight:</b>",
            ui_scale(pygame.Rect((0, 15), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.tag_element["tag_display"]
            }
        )
        self.weight_element["weight_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0, 18), (50, 29))),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.tag_element["tag_display"],
                "left_target": self.weight_element["weight_text"]
            },
            initial_text=f"{self.weight_info}"
        )
        self.create_divider(self.weight_element["weight_entry"], "weight", -10)

    def create_tag_editor(self):
        if not self.tag_element.get("tag_container"):
            self.tag_element["tag_container"] = UICollapsibleContainer(
                ui_scale(pygame.Rect((0, 0), (440, 0))),
                top_button_oriented_left=False,
                title_text="<b>Tags:</b>",
                scrolling_container_to_reset=self.editor_container,
                manager=MANAGER,
                container=self.editor_container,
                anchors={
                    "top_target": self.type_element["sub_display"]
                }
            )
            self.tag_element["tag_container"].close()
            self.tag_element["basic_checkbox_container"] = pygame_gui.elements.UIAutoResizingContainer(
                ui_scale(pygame.Rect((48, 0), (0, 0))),
                container=self.tag_element["tag_container"],
                manager=MANAGER,
                anchors={
                    "top_target": self.tag_element["tag_container"].top_button
                }
            )

        self.update_basic_checkboxes()

        if not self.rank_tag_checkbox.get("rank_tag_text"):
            self.rank_tag_checkbox["rank_tag_text"] = UITextBoxTweaked(
                "screens.event_edit.rank_tags",
                ui_scale(pygame.Rect((0, 10), (250, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.tag_element["tag_container"],
                anchors={
                    "top_target": self.tag_element["basic_checkbox_container"],
                    "left_target": self.event_id_element["event_id_text"],

                }
            )
            prev_element = None
            rank_list = Cat.rank_sort_order.copy()
            rank_list.append("apps")
            for rank in rank_list:
                self.rank_tag_checkbox[rank] = UICheckbox(
                    position=(400, 10),
                    container=self.tag_element["tag_container"],
                    manager=MANAGER,
                    check=False,
                    anchors={
                        "top_target": (prev_element if
                                       prev_element else
                                       self.rank_tag_checkbox["rank_tag_text"]),
                    }
                )

                check_box_rect = pygame.Rect((0, 10), (350, -1))
                check_box_rect.right = -70
                if rank == "apps":
                    rank_string = f"two of any apprentice type"
                else:
                    rank_string = f"two {rank}s" if rank not in ("deputy", "leader") else rank
                self.rank_tag_checkbox[f"{rank}_text"] = UITextBoxTweaked(
                    rank_string,
                    ui_scale(check_box_rect),
                    object_id="#text_box_30_horizright_pad_10_10",
                    line_spacing=1,
                    manager=MANAGER,
                    container=self.tag_element["tag_container"],
                    anchors={
                        "top_target": (prev_element if
                                       prev_element else
                                       self.rank_tag_checkbox["rank_tag_text"]),
                        "right": "right"
                    }
                )

                prev_element = self.rank_tag_checkbox[f"{rank}_text"]

        if not self.tag_element.get("tag_display"):
            self.tag_element["tag_display"] = UITextBoxTweaked(
                "chosen tags: []",
                ui_scale(pygame.Rect((10, 10), (440, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                manager=MANAGER,
                container=self.editor_container,
                anchors={
                    "top_target": self.tag_element["tag_container"],
                },
                allow_split_dashes=False
            )
            self.create_divider(self.tag_element["tag_display"], "tag", -14)

    def update_basic_checkboxes(self):
        prev_element = None

        # clear old elements
        if self.basic_tag_checkbox:
            for info in self.basic_tag_list:
                if self.basic_tag_checkbox.get(f"{info['tag']}_text"):
                    self.basic_tag_checkbox[f"{info['tag']}_text"].kill()
                if self.basic_tag_checkbox.get(info["tag"]):
                    self.basic_tag_checkbox[info["tag"]].kill()

        # make new ones!
        for info in self.basic_tag_list:
            # first reset the values
            if info.get("required_type") and info["required_type"] != self.type_info[0]:
                if self.tag_element["tag_container"].is_open:
                    self.tag_element["tag_container"].close()

                # this is to change the setting to false
                index = self.basic_tag_list.index(info)
                self.basic_tag_list[index] = {
                    "tag": info["tag"],
                    "setting": False,
                    "required_type": info["required_type"],
                    "conflict": info["conflict"]
                }
                continue

            self.basic_tag_checkbox[f"{info['tag']}_text"] = UITextBoxTweaked(
                f"screens.event_edit.{info['tag']}",
                ui_scale(pygame.Rect((0, 10), (350, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.tag_element["basic_checkbox_container"],
                anchors={
                    "top_target": prev_element,
                } if prev_element else None
            )

            self.basic_tag_checkbox[info["tag"]] = UICheckbox(
                position=(350, 10),
                container=self.tag_element["basic_checkbox_container"],
                manager=MANAGER,
                check=info["setting"],
                anchors={
                    "top_target": prev_element
                } if prev_element else None
            )

            prev_element = self.basic_tag_checkbox[f"{info['tag']}_text"]

        self.update_tag_info()

    def update_sub_buttons(self, type_list):

        if not self.type_element.get("subtype_dropdown"):
            self.type_element["subtype_dropdown"] = UIDropDown(
                pygame.Rect((0, 17), (150, 30)),
                parent_text="pick subtypes",
                item_list=type_list,
                manager=MANAGER,
                container=self.editor_container,
                multiple_choice=True,
                disable_selection=False,
                child_trigger_close=False,
                starting_height=3,
                anchors={
                    "left_target": self.type_element["pick_type"],
                    "top_target": self.season_element["season_display"]
                }
            )
        else:
            self.type_element["subtype_dropdown"].new_item_list(type_list)

    def create_type_editor(self):
        self.type_element["type_text"] = UITextBoxTweaked(
            "<b>* sub/type:</b>",
            ui_scale(pygame.Rect((0, 14), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.season_element["season_display"]
            }
        )
        if not self.type_info:
            self.type_info = ["death"]

        self.type_element["pick_type"] = UIDropDown(
            pygame.Rect((17, 17), (150, 30)),
            parent_text=self.type_info[0],
            item_list=list(self.event_types.keys()),
            container=self.editor_container,
            anchors={
                "left_target": self.event_id_element["event_id_text"],
                "top_target": (self.season_element["season_display"])
            },
            starting_height=3,
            manager=MANAGER,
            child_trigger_close=True,
            starting_selection=self.type_info
        )

        self.update_sub_buttons(self.event_types[self.type_info[0]])

        self.type_element["sub_display"] = UITextBoxTweaked(
            "chosen subtypes: []",
            ui_scale(pygame.Rect((10, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.type_element["type_text"],
            },
            allow_split_dashes=False
        )
        self.create_divider(self.type_element["sub_display"], "type", -14)

    def create_season_editor(self):
        self.season_element["season_text"] = UITextBoxTweaked(
            "screens.event_edit.season_info",
            ui_scale(pygame.Rect((0, 10), (250, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.location_element["location_display"]
            }
        )

        self.season_element["season_dropdown"] = UIDropDown(
            pygame.Rect((10, 20), (150, 30)),
            parent_text="choices",
            item_list=self.all_seasons,
            container=self.editor_container,
            manager=MANAGER,
            multiple_choice=True,
            disable_selection=False,
            child_trigger_close=False,
            starting_height=5,
            anchors={
                "left_target": self.season_element["season_text"],
                "top_target": self.location_element["location_display"]
            }
        )

        self.season_element["season_display"] = UITextBoxTweaked(
            "chosen season: ['any']",
            ui_scale(pygame.Rect((10, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.season_element["season_text"],
            },
            allow_split_dashes=False
        )
        self.create_divider(self.season_element["season_display"], "season", -14)

    def create_location_editor(self):
        self.location_element["location_text"] = UITextBoxTweaked(
            "screens.event_edit.location_info",
            ui_scale(pygame.Rect((0, 10), (450, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.event_id_element["event_id_text"]
            }
        )
        biome_list = game.clan.BIOME_TYPES
        prev_element = None
        for biome in biome_list:
            y_pos = 10 if not prev_element else -2
            self.location_element[biome] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, y_pos), (150, 30))),
                biome,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "left_target": self.event_id_element["event_id_text"],
                    "top_target": (self.location_element["location_text"]
                                   if not prev_element
                                   else prev_element)
                }
            )
            prev_element = self.location_element[biome]

        self.location_element["location_display"] = UITextBoxTweaked(
            "chosen location: ['any']",
            ui_scale(pygame.Rect((10, 10), (440, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": (self.location_element[biome_list[-1]]),
            },
            allow_split_dashes=False
        )
        self.create_divider(self.location_element["location_display"], "location", -14)

    def update_camp_list(self, chosen_biome):

        for biome in self.all_camps:
            for camp in self.all_camps[biome]:
                if self.location_element.get(camp):
                    self.location_element[camp].kill()

        camp_list = self.all_camps.get(chosen_biome)

        if not camp_list:
            return

        prev_element = None
        for camp in camp_list:
            y_pos = 10 if not prev_element else -2
            self.location_element[camp] = UISurfaceImageButton(
                ui_scale(pygame.Rect((20, y_pos), (150, 30))),
                camp,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "left_target": self.location_element[chosen_biome],
                    "top_target": (self.location_element["location_text"]
                                   if not prev_element
                                   else prev_element)
                }
            )
            prev_element = self.location_element[camp]

    def create_event_id_editor(self):
        # TODO: add a way to detect if inputted event_id is a dupe
        self.event_id_element["event_id_text"] = UITextBoxTweaked(
            "<b>* event_id:</b>",
            ui_scale(pygame.Rect((0, 10), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )
        self.event_id_element["event_id_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0, 13), (300, 29))),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "left_target": self.event_id_element["event_id_text"]
            },
            placeholder_text="screens.event_edit.empty_event_id"
        )
        self.create_divider(self.event_id_element["event_id_text"], "event_id")
